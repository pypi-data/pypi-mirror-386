# Adapted from https://github.com/Dao-AILab/quack/blob/3d0ab3ec2164749caac8f269f771e66a40efd2de/quack/rmsnorm.py
from typing import Optional

import cuda.bindings.driver as cuda

from typing import Tuple
from functools import partial

import cutlass
import cutlass.cute as cute
from cutlass import Float32
from cutlass import const_expr
from cutlass.cute.runtime import from_dlpack

import torch
from torch import Tensor

import b10_kernel.cute.utils as utils
import b10_kernel.cute.copy_utils as copy_utils
from b10_kernel.cute.utils import torch2cute_dtype_map
from b10_kernel.cute.reduction_base import ReductionBase
from b10_kernel.cute.reduce import row_reduce


class RMSNorm(ReductionBase):
    def __init__(self, dtype: cutlass.Numeric, N: int):
        super().__init__(dtype, N, stage=1)
        self.reload_from = None if N <= 8192 else "smem"
        self.delay_w_load = False

    def _calculate_threads_per_row(self):
        """Calculate the number of threads per row for the RMSNorm kernel."""
        N = self.N
        if N <= 64:
            return 8
        elif N <= 128:
            return 16
        elif N <= 3072:
            return 32
        elif N <= 6144:
            return 64
        elif N <= 16384:
            return 128
        else:
            return 256

    def _set_cluster_n(self):
        """
        Set the number of clusters for the RMSNorm kernel.
        Stored in self.cluster_n.
        """
        N = self.N

        # cluster_n = 4 is faster and cluster_n = 2 for N=64k for some reason
        # Similarly cluster_n = 8 is faster for N=128k
        if const_expr(self.dtype.width == 16):
            # 16-bit types (fp16, bf16)
            if N <= 16 * 1024:
                cluster_n = 1
            elif N <= 32 * 1024:
                cluster_n = 2
            elif N <= 64 * 1024:
                cluster_n = 4
            elif N <= 128 * 1024:
                cluster_n = 8
            else:
                cluster_n = 16
        else:
            # 32-bit types (fp32)
            if N <= 32 * 1024:
                cluster_n = 1
            elif N <= 64 * 1024:
                cluster_n = 2
            elif N <= 128 * 1024:
                cluster_n = 4
            elif N <= 256 * 1024:
                cluster_n = 8
            else:
                cluster_n = 16

        self.cluster_n = cluster_n

    def _smem_size_in_bytes(self, tiler_mn, num_warps, dtype_res=None):
        return (
            cute.size_in_bytes(self.dtype, cute.make_layout(tiler_mn))
            + (
                cute.size_in_bytes(dtype_res, cute.make_layout(tiler_mn))
                if dtype_res is not None
                else 0
            )
            + self.stage
            * num_warps
            * self.cluster_n
            * (self.reduction_dtype.width // 8)
            + self.stage * (cutlass.Int64.width // 8)
        )

    @cute.jit
    def __call__(
        self,
        mX: cute.Tensor,
        mW: Optional[cute.Tensor],
        mB: Optional[cute.Tensor],
        mRes: Optional[cute.Tensor],
        mO: cute.Tensor,
        mResO: Optional[cute.Tensor],
        mRstd: Optional[cute.Tensor],
        stream: cuda.CUstream,
        eps: Float32 = 1e-6,
    ):
        semistatic_shape = (
            *mX.shape[:-1],
            self.N,
        )  # Set last dimension to be statically N
        new_stride = lambda t: (
            cute.assume(t.stride[0], divby=128 // t.element_type.width),
            t.stride[1],
        )
        mX, mRes, mO, mResO = [
            cute.make_tensor(
                t.iterator, cute.make_layout(semistatic_shape, stride=new_stride(t))
            )
            if const_expr(t is not None)
            else None
            for t in (mX, mRes, mO, mResO)
        ]
        assert mX.element_type == self.dtype
        assert mO.element_type == self.dtype
        self._set_cluster_n()
        largest_dtype_width = const_expr(
            max(
                mX.element_type.width,
                mRes.element_type.width if mRes is not None else 0,
                mO.element_type.width,
                mResO.element_type.width if mResO is not None else 0,
            )
        )
        tiler_mn, tv_layout = self._get_tv_layout(
            num_copy_bits=128 // largest_dtype_width * mX.element_type.width
        )
        num_threads = cute.size(tv_layout, mode=[0])
        num_warps = num_threads // cute.arch.WARP_SIZE
        if const_expr(mW is not None):
            mW_expanded_layout = cute.prepend(
                mW.layout, cute.make_layout((tiler_mn[0],), stride=(0,))
            )
            mW = cute.make_tensor(mW.iterator, mW_expanded_layout)
        if const_expr(mB is not None):
            mB_expanded_layout = cute.prepend(
                mB.layout, cute.make_layout((tiler_mn[0],), stride=(0,))
            )
            mB = cute.make_tensor(mB.iterator, mB_expanded_layout)
        if const_expr(mRstd is not None):
            mRstd_expanded_layout = cute.append(
                mRstd.layout, cute.make_layout((self.N,), stride=(0,))
            )
            mRstd = cute.make_tensor(mRstd.iterator, mRstd_expanded_layout)
        self.kernel(
            mX,
            mW,
            mB,
            mRes,
            mO,
            mResO,
            mRstd,
            eps,
            tv_layout,
            tiler_mn,
            self.reload_from,
        ).launch(
            grid=[cute.ceil_div(mX.shape[0], tiler_mn[0]), self.cluster_n, 1],
            block=[num_threads, 1, 1],
            cluster=(
                [1, self.cluster_n, 1] if const_expr(self.cluster_n > 1) else None
            ),
            smem=self._smem_size_in_bytes(
                tiler_mn,
                num_warps,
                dtype_res=mRes.element_type if mRes is not None else None,
            ),
            stream=stream,
        )

    @cute.kernel
    def kernel(
        self,
        mX: cute.Tensor,
        mW: Optional[cute.Tensor],
        mB: Optional[cute.Tensor],
        mRes: Optional[cute.Tensor],
        mO: cute.Tensor,
        mResO: Optional[cute.Tensor],
        mRstd: Optional[cute.Tensor],
        eps: cute.Float32,
        tv_layout: cute.Layout,
        tiler_mn: cute.Shape,
        reload_from: cutlass.Constexpr = None,
        delay_w_load: cutlass.Constexpr = False,
    ):
        tidx, _, _ = cute.arch.thread_idx()
        bidx, _, _ = cute.arch.block_idx()
        if const_expr(self.cluster_n > 1):
            cluster_y = cute.arch.block_idx()[1]
        else:
            cluster_y = const_expr(0)

        smem = cutlass.utils.SmemAllocator()
        sX = smem.allocate_tensor(
            mX.element_type,
            cute.make_ordered_layout(tiler_mn, order=(1, 0)),
            byte_alignment=16,
        )
        if const_expr(mRes is not None):
            sRes = smem.allocate_tensor(
                mRes.element_type,
                cute.make_ordered_layout(tiler_mn, order=(1, 0)),
                byte_alignment=16,
            )
        reduction_buffer, mbar_ptr = self._allocate_reduction_buffer_and_mbar(
            smem, tv_layout
        )

        shape = mX.shape
        idX = cute.make_identity_tensor(shape)
        # slice for CTAs
        # We use domain_offset_i64 to deal with tensors larger than 2^31 elements
        mX, mRes, mO, mResO = [
            utils.domain_offset_i64((bidx * tiler_mn[0], 0), mT)
            if mT is not None
            else None
            for mT in (mX, mRes, mO, mResO)
        ]
        gX, gRes, gO, gResO = [
            cute.local_tile(mT, tiler_mn, (0, cluster_y)) if mT is not None else None
            for mT in (mX, mRes, mO, mResO)
        ]
        cX = cute.local_tile(idX, tiler_mn, (bidx, cluster_y))
        gW, gB = [
            cute.local_tile(mT, tiler_mn, (0, cluster_y))
            if const_expr(mT is not None)
            else None
            for mT in (mW, mB)
        ]
        gRstd = (
            cute.local_tile(mRstd, tiler_mn, (bidx, cluster_y))
            if const_expr(mRstd is not None)
            else None
        )

        # declare the atoms which will be used later for memory copy
        num_copy_elems_X = tv_layout.shape[1][0]
        copy_atom_load_X_async = copy_utils.get_copy_atom(
            mX.element_type, num_copy_elems_X, is_async=True
        )
        thr_copy_X = cute.make_tiled_copy(
            copy_atom_load_X_async, tv_layout, tiler_mn
        ).get_slice(tidx)

        tXgW = thr_copy_X.partition_S(gW) if const_expr(mW is not None) else None
        tXgB = thr_copy_X.partition_S(gB) if const_expr(mB is not None) else None
        tXgX = thr_copy_X.partition_S(gX)
        tXsX = thr_copy_X.partition_D(sX)
        if const_expr(mRes is not None):
            tXgRes = thr_copy_X.partition_S(gRes)
            tXsRes = thr_copy_X.partition_D(sRes)
        tXgO = thr_copy_X.partition_D(gO)
        if const_expr(mResO is not None):
            tXgResO = thr_copy_X.partition_D(gResO)
        tXrRstd = (
            thr_copy_X.partition_D(gRstd) if const_expr(mRstd is not None) else None
        )
        tXcX = thr_copy_X.partition_S(cX)[(0, None), None, None]

        # allocate fragments for gmem->rmem
        tXrW = cute.make_fragment_like(tXgW) if const_expr(mW is not None) else None
        if const_expr(mW is not None):
            tXrW.fill(0.0)
        tXrB = cute.make_fragment_like(tXgB) if const_expr(mB is not None) else None
        tXrX, tXrO = [cute.make_fragment_like(t) for t in (tXgX, tXgO)]
        if const_expr(mRes is not None):
            tXrRes = cute.make_fragment_like(tXgRes)

        num_warps = cute.size(tv_layout, mode=[0]) // cute.arch.WARP_SIZE
        self._initialize_cluster(tidx, mbar_ptr, num_warps)

        is_even_N = cutlass.const_expr(shape[1] == tiler_mn[1] * self.cluster_n)
        tXpX = (
            utils.predicate_k(thr_copy_X.partition_S(cX), limit=shape[1])
            if not is_even_N
            else None
        )
        # Each copy will use the same number of elements as X and same predicate
        copy = partial(copy_utils.copy, pred=tXpX, num_copy_elems=num_copy_elems_X)

        row = tXcX[0][0]
        if row < shape[0]:
            copy(tXgX, tXsX, is_async=True)
            if const_expr(mRes is not None):
                copy(tXgRes, tXsRes, is_async=True)
        cute.arch.cp_async_commit_group()

        if const_expr(not delay_w_load):
            if const_expr(mW is not None):
                copy(tXgW, tXrW)
            if const_expr(mB is not None):
                copy(tXgB, tXrB)

        cute.arch.cp_async_wait_group(0)
        cute.autovec_copy(tXsX, tXrX)
        x = tXrX.load().to(cute.Float32)
        if const_expr(mRes is not None):
            cute.autovec_copy(tXsRes, tXrRes)
            x += tXrRes.load().to(cute.Float32)
        if const_expr(mResO is not None):
            tXrResO = cute.make_fragment_like(tXgResO)
            tXrResO.store(x.to(tXrResO.element_type))
            if row < shape[0]:
                copy(tXrResO, tXgResO)

        threads_per_row = tv_layout.shape[0][0]
        sum_sq_x = row_reduce(
            x * x,
            cute.ReductionOp.ADD,
            threads_per_row,
            reduction_buffer[None, None, 0],
            mbar_ptr,
            init_val=0.0,
            hook_fn=(
                cute.arch.cluster_wait if const_expr(self.cluster_n > 1) else None
            ),
        )
        rstd = cute.math.rsqrt(sum_sq_x / shape[1] + eps, fastmath=True)
        if const_expr(mRstd is not None):
            # Only the thread corresponding to column 0 writes out the rstd to gmem
            if (
                tXcX[0][1] == 0
                and row < shape[0]
                and (self.cluster_n == 1 or cute.arch.block_idx_in_cluster() == 0)
            ):
                tXrRstd[0] = rstd
        if const_expr(delay_w_load):
            if const_expr(mW is not None):
                copy(tXgW, tXrW)
            if const_expr(mB is not None):
                copy(tXgB, tXrB)
        if const_expr(reload_from == "smem" or reload_from == "gmem"):
            if const_expr(reload_from == "smem"):
                cute.autovec_copy(tXsX, tXrX)
            else:
                copy(tXgX, tXrX)
            x = tXrX.load().to(cute.Float32)
            if const_expr(mRes is not None):
                cute.autovec_copy(tXsRes, tXrRes)
                x += tXrRes.load().to(cute.Float32)
        x_hat = x * rstd
        y = x_hat
        if const_expr(mW is not None):
            y *= tXrW.load().to(cute.Float32)
        if const_expr(mB is not None):
            y += tXrB.load().to(cute.Float32)
        tXrO.store(y.to(tXrO.element_type))
        if row < shape[0]:
            copy(tXrO, tXgO)


def _rmsnorm_fwd(
    x: Tensor,
    weight: Optional[Tensor],
    out: Tensor,
    bias: Optional[Tensor] = None,
    rstd: Optional[Tensor] = None,
    residual: Optional[Tensor] = None,
    residual_out: Optional[Tensor] = None,
    eps: float = 1e-6,
) -> None:
    """RMSNorm forward pass.
    Args:
        x: Input tensor of shape (M, N)
        weight: Optional weight tensor of shape (N,)
        eps: Small value for numerical stability
    Returns:
        Normalized output tensor of same shape as x
    """
    assert x.dim() == 2, "Input must be 2D"
    assert x.is_cuda, "Input tensor must be on CUDA device"
    assert x.dtype in [torch.float16, torch.bfloat16, torch.float32], (
        "Unsupported dtype"
    )
    if weight is not None:
        assert weight.dim() == 1, "Weight must be 1D"
        assert x.shape[-1] == weight.shape[0], (
            "Last dimension of input must match weight dimension"
        )
        assert weight.is_cuda, "Weight tensor must be on CUDA device"
        assert weight.dtype in [
            torch.float32,
            torch.bfloat16,
            torch.float16,
        ], "Weight must be float32, float16 or bfloat16"
    if residual is not None:
        assert residual.shape == x.shape
        assert residual.is_cuda
        assert residual.dtype in [
            torch.float16,
            torch.bfloat16,
            torch.float32,
        ], "Residual must be float16, bfloat16, or float32"

    _, N = x.shape
    device = x.device
    dtype = torch2cute_dtype_map[x.dtype]
    convert_from_dlpack = lambda x: (
        from_dlpack(x.detach(), assumed_align=16).mark_layout_dynamic(leading_dim=1)
    )
    x_tensor, res_tensor, out_tensor, res_out_tensor = [
        convert_from_dlpack(t) if t is not None else None
        for t in (x, residual, out, residual_out)
    ]
    # handle weight divisibility based on weight dtype
    if weight is not None:
        weight_dtype = torch2cute_dtype_map[weight.dtype]
        weight_tensor = utils.convert_from_dlpack(
            weight.detach(), leading_dim=0, divisibility=128 // weight_dtype.width
        )
    else:
        weight_tensor = None
    if bias is not None:
        bias_dtype = torch2cute_dtype_map[bias.dtype]
        bias_tensor = utils.convert_from_dlpack(
            bias.detach(), leading_dim=0, divisibility=128 // bias_dtype.width
        )
    else:
        bias_tensor = None
    rstd_tensor = (
        from_dlpack(rstd.detach(), assumed_align=4).mark_layout_dynamic(leading_dim=0)
        if rstd is not None
        else None
    )
    current_stream = cuda.CUstream(torch.cuda.current_stream().cuda_stream)
    compile_key = (
        N,
        dtype,
        res_tensor.element_type if residual is not None else None,
        weight_tensor.element_type if weight is not None else None,
        bias_tensor.element_type if bias is not None else None,
        res_out_tensor.element_type if residual_out is not None else None,
        rstd is not None,
    )
    if compile_key not in _rmsnorm_fwd.compile_cache:
        rmsnorm_op = RMSNorm(dtype, N)
        _rmsnorm_fwd.compile_cache[compile_key] = cute.compile(
            rmsnorm_op,
            x_tensor,
            weight_tensor,
            bias_tensor,
            res_tensor,
            out_tensor,
            res_out_tensor,
            rstd_tensor,
            current_stream,
            eps,
        )
    _rmsnorm_fwd.compile_cache[compile_key](
        x_tensor,
        weight_tensor,
        bias_tensor,
        res_tensor,
        out_tensor,
        res_out_tensor,
        rstd_tensor,
        current_stream,
        eps,
    )


_rmsnorm_fwd.compile_cache = {}


def rmsnorm_fwd(
    x: Tensor,
    weight: Optional[Tensor] = None,
    bias: Optional[Tensor] = None,
    residual: Optional[Tensor] = None,
    out_dtype: Optional[torch.dtype] = None,
    residual_dtype: Optional[torch.dtype] = None,
    eps: float = 1e-6,
    store_rstd: bool = False,
) -> Tuple[Tensor, Tensor, Optional[Tensor]]:
    # Need to wrap to handle the case where residual_out is a alias of x, which makes torch.library
    # and torch.compile unhappy. Also allocate memory for out and residual_out if they are None
    # so that _layer_norm_fwd_impl doesn't have to return them.
    out_dtype = x.dtype if out_dtype is None else out_dtype
    out = torch.empty_like(x, dtype=out_dtype)
    rstd = (
        torch.empty(x.shape[0], device=x.device, dtype=torch.float32)
        if store_rstd
        else None
    )
    if residual is not None:
        residual_dtype = residual.dtype
    if residual is not None or (
        residual_dtype is not None and residual_dtype != x.dtype
    ):
        residual_out = torch.empty_like(
            x, dtype=residual_dtype if residual_dtype is not None else x.dtype
        )
    else:
        residual_out = None
    _rmsnorm_fwd(x, weight, out, bias, rstd, residual, residual_out, eps=eps)
    # residual_out is None if residual is None and residual_dtype == input_dtype and dropout_p == 0.0
    if residual_out is None:
        residual_out = x
    return out, residual_out, rstd


_rmsnorm_fwd.compile_cache = {}


def rmsnorm(x: torch.Tensor, weight: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    """RMSNorm forward pass with automatic differentiation support.

    Args:
        x: Input tensor of shape (M, N)
        weight: Weight tensor of shape (N,)
        eps: Small value for numerical stability

    Returns:
        Normalized output tensor of same shape as x
    """
    x_shape_start = x.shape
    x = x.view(-1, x.shape[-1])

    out_dtype = x.dtype
    out = torch.empty_like(x, dtype=out_dtype)

    _rmsnorm_fwd(x=x, weight=weight, out=out, eps=eps)

    return out.reshape(x_shape_start)
