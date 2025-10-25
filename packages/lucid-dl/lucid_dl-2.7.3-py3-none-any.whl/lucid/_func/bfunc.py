from functools import partial
from types import ModuleType
import math
import numpy as np

import lucid
from lucid._tensor import Tensor
from lucid.types import _Gradient, _ShapeLike

from lucid._backend.core import (
    operation,
    binary_func_op,
    _FuncOpReturnType,
    _GradFuncType,
)
from lucid._backend.metal import mx


def _broadcast_flops(a: Tensor, b: Tensor) -> int:
    out_shape = np.broadcast_shapes(a.shape, b.shape)
    return int(np.prod(out_shape))


class add(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data + b.data)
        return self.result, self.__grad__

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.add(a.data, b.data))
        return self.result, self.__grad__

    def __grad__(self) -> _GradFuncType:
        return self.result.grad, self.result.grad

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return _broadcast_flops(a, b)


class sub(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data - b.data)
        return self.result, self.__grad__

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.subtract(a.data, b.data))
        return self.result, self.__grad__

    def __grad__(self) -> _GradFuncType:
        return self.result.grad, -self.result.grad

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return _broadcast_flops(a, b)


class multiply(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data * b.data)
        return self.result, partial(self.__grad__, a=a, b=b)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.multiply(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b)

    def __grad__(self, a: Tensor, b: Tensor) -> _GradFuncType:
        return b.data * self.result.grad, a.data * self.result.grad

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return _broadcast_flops(a, b)


class truediv(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data / b.data)
        return self.result, partial(self.__grad__, a=a, b=b)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.divide(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b)

    def __grad__(self, a: Tensor, b: Tensor) -> _GradFuncType:
        return (
            (1 / b.data) * self.result.grad,
            (-a.data / (b.data**2)) * self.result.grad,
        )

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return _broadcast_flops(a, b)


class floordiv(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data // b.data).astype(lucid.Int)
        return self.result, partial(self.__grad__, lib_=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data // b.data).astype(lucid.Int)
        return self.result, partial(self.__grad__, lib_=mx)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return _broadcast_flops(a, b)


class _equal(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> Tensor:
        self.result = Tensor(a.data == b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> Tensor:
        self.result = Tensor(a.data == b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=mx)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)


class _not_equal(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> Tensor:
        self.result = Tensor(a.data != b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> Tensor:
        self.result = Tensor(a.data != b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)


class _greater(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data > b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data > b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)


class _greater_or_equal(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data >= b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data >= b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)


class _less(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data < b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data < b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)


class _less_or_equal(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data <= b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(a.data <= b.data).astype(bool)
        return self.result, partial(self.__grad__, lib=np)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)


class minimum(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(np.minimum(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.minimum(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b)

    def __grad__(self, a: Tensor, b: Tensor) -> _GradFuncType:
        a_grad = (a.data <= b.data).astype(a.data.dtype)
        b_grad = (a.data > b.data).astype(b.data.dtype)

        return a_grad * self.result.grad, b_grad * self.result.grad

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return _broadcast_flops(a, b)


class maximum(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(np.maximum(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.maximum(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b)

    def __grad__(self, a: Tensor, b: Tensor) -> _GradFuncType:
        a_grad = (a.data >= b.data).astype(a.data.dtype)
        b_grad = (a.data < b.data).astype(b.data.dtype)

        return a_grad * self.result.grad, b_grad * self.result.grad

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return _broadcast_flops(a, b)


class power(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(np.power(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b, lib_=np)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.power(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b, lib_=mx)

    def __grad__(self, a: Tensor, b: Tensor, lib_: ModuleType) -> _GradFuncType:
        a_grad = b.data * lib_.power(a.data, b.data - 1)
        b_grad = lib_.power(a.data, b.data) * lib_.log(a.data)

        return a_grad * self.result.grad, b_grad * self.result.grad

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return _broadcast_flops(a, b)


class dot(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(np.dot(a.data, b.data))
        return self.result, partial(self.__grad_cpu__, a=a, b=b)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        if a.ndim != 1 or b.ndim != 1:
            raise ValueError(f"Only 1D dot product is supported for Metal backend.")

        self.result = Tensor(mx.sum(a.data * b.data))
        return self.result, partial(self.__grad_gpu__, a=a, b=b)

    def __grad_cpu__(self, a: Tensor, b: Tensor) -> _GradFuncType:
        return self.result.grad.dot(b.data.mT), a.data.mT.dot(self.result.grad)

    def __grad_gpu__(self, a: Tensor, b: Tensor) -> _GradFuncType:
        return b.data * self.result.grad, a.data * self.result.grad

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        if a.ndim == 1 and b.ndim == 1:
            return 2 * a.shape[0] - 1

        a_batch_dims = a.shape[:-2] if a.ndim > 2 else ()
        b_batch_dims = b.shape[:-2] if b.ndim > 2 else ()

        m = a.shape[-2] if a.ndim >= 2 else 1
        k = a.shape[-1] if a.ndim >= 1 else 1
        k_b = b.shape[-2] if b.ndim >= 2 else 1
        n = b.shape[-1] if b.ndim >= 2 else 1

        if k != k_b:
            raise ValueError("Incompatible shapes for dot product.")

        batch_size = 1
        if a_batch_dims or b_batch_dims:
            max_dims = max(len(a_batch_dims), len(b_batch_dims))
            a_padded = (1,) * (max_dims - len(a_batch_dims)) + a_batch_dims
            b_padded = (1,) * (max_dims - len(b_batch_dims)) + b_batch_dims

            for a_dim, b_dim in zip(a_padded, b_padded):
                batch_size *= max(a_dim, b_dim)

        return batch_size * m * n * (2 * k - 1)


class inner(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(np.inner(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b, lib=np)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.inner(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b, lib=mx)

    def __grad__(self, a: Tensor, b: Tensor, lib_: ModuleType) -> _GradFuncType:
        return (
            lib_.tensordot(self.result.grad, b.data, axes=([-1], [-1])),
            lib_.tensordot(a.data, self.result.grad, axes=([-1], [-1])),
        )

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        if a.ndim == 1 and b.ndim == 1:
            n = a.shape[0]
            return 2 * n - 1

        elif a.ndim >= 1 and b.ndim >= 1:
            n = a.shape[-1]
            if b.shape[-1] != n:
                raise ValueError("Last dimensions must match for inner product")

            out_shape = list(a.shape[:-1]) + list(b.shape[:-1])
            output_size = math.prod(out_shape)
            return output_size * (2 * n - 1)


class outer(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(np.outer(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b, lib_=np)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.outer(a.data, b.data))
        return self.result, partial(self.__grad__, a=a, b=b, lib_=mx)

    def __grad__(self, a: Tensor, b: Tensor, lib_: ModuleType) -> _GradFuncType:
        return (
            lib_.tensordot(self.result.grad, b.data, axes=([1], [0])),
            lib_.tensordot(self.result.grad, a.data, axes=([0], [0])),
        )

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        return a.size * b.size


class matmul(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        out = np.matmul(a.data, b.data)
        self.result = Tensor(out)
        return self.result, partial(self.__grad__, a=a, b=b, lib_=np)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        out = mx.matmul(a.data, b.data)
        self.result = Tensor(out)
        return self.result, partial(self.__grad__, a=a, b=b, lib_=mx)

    def __grad__(self, a: Tensor, b: Tensor, lib_: ModuleType) -> _GradFuncType:
        grad = self.result.grad
        if grad.ndim == 0:
            grad = lib_.reshape(grad, (1, 1))

        grad_a = lib_.matmul(grad, lib_.swapaxes(b.data, -1, -2))
        grad_b = lib_.matmul(lib_.swapaxes(a.data, -1, -2), grad)

        grad_a = self._reduce_broadcast_shape(grad_a, a.shape, lib_)
        grad_b = self._reduce_broadcast_shape(grad_b, b.shape, lib_)

        return grad_a, grad_b

    def _reduce_broadcast_shape(
        self, grad: _Gradient, ref_shape: _ShapeLike, lib_: ModuleType
    ) -> _Gradient:
        while len(grad.shape) > len(ref_shape):
            grad = grad.sum(axis=0, keepdims=False)

        for i, (gdim, rdim) in enumerate(zip(grad.shape, ref_shape)):
            if gdim != rdim:
                grad = grad.sum(axis=i, keepdims=True)

        grad = lib_.reshape(grad, ref_shape)
        return grad

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        a_shape, b_shape = a.shape, b.shape

        m = a_shape[-2] if len(a_shape) >= 2 else 1
        k = a_shape[-1] if len(a_shape) >= 1 else 1
        n = b_shape[-1] if len(b_shape) >= 1 else 1

        a_batch = (
            (1,) * (len(b_shape) - len(a_shape)) + a_shape[:-2]
            if len(a_shape) > 2
            else (1,) * (len(b_shape) - len(a_shape))
        )
        b_batch = (
            (1,) * (len(a_shape) - len(b_shape)) + b_shape[:-2]
            if len(b_shape) > 2
            else (1,) * (len(a_shape) - len(b_shape))
        )
        batch_shape = [max(x, y) for x, y in zip(a_batch, b_batch)]
        batch_size = np.prod(batch_shape) if batch_shape else 1

        return batch_size * m * n * k


class tensordot(operation):
    def __init__(
        self, axes: int | tuple[int, int] | tuple[list[int], list[int]]
    ) -> None:
        super().__init__()
        self.axes = axes

    def _get_axes_lists(self) -> tuple[list[int], list[int]]:
        if isinstance(self.axes, int):
            return [self.axes], [self.axes]

        if isinstance(self.axes, tuple):
            if len(self.axes) == 2 and all(isinstance(x, int) for x in self.axes):
                return [self.axes[0]], [self.axes[1]]
            elif len(self.axes) == 2 and all(isinstance(x, list) for x in self.axes):
                return list(self.axes[0]), list(self.axes[1])
            else:
                raise ValueError("Invalid axes format for tensordot operation.")

    @binary_func_op()
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        axes_a, axes_b = self._get_axes_lists()
        self.result = Tensor(np.tensordot(a.data, b.data, axes=(axes_a, axes_b)))
        return self.result, partial(self.__grad__, a=a, b=b, lib_=np)

    @binary_func_op(device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        axes_a, axes_b = self._get_axes_lists()
        self.result = Tensor(mx.tensordot(a.data, b.data, axes=(axes_a, axes_b)))
        return self.result, partial(self.__grad__, a=a, b=b, lib_=mx)

    def __grad__(self, a: Tensor, b: Tensor, lib_: ModuleType) -> _GradFuncType:
        axes_a, axes_b = self._get_axes_lists()
        grad = self.result.grad

        free_axes_a = [i for i in range(a.ndim) if i not in axes_a]
        free_axes_b = [i for i in range(b.ndim) if i not in axes_b]

        grad_a = lib_.tensordot(
            grad, b.data, axes=(list(range(len(free_axes_a), grad.ndim)), free_axes_b)
        )
        perm_a = free_axes_a + axes_a
        inv_perm_a = [perm_a.index(i) for i in range(a.ndim)]
        grad_a = lib_.transpose(grad_a, inv_perm_a)

        grad_b = lib_.tensordot(
            a.data, grad, axes=(free_axes_a, list(range(len(free_axes_a))))
        )
        perm_b = axes_b + free_axes_b
        inv_perm_b = [perm_b.index(i) for i in range(b.ndim)]
        grad_b = lib_.transpose(grad_b, inv_perm_b)

        return grad_a, grad_b

    def __flops__(self, a: Tensor, b: Tensor) -> int:
        axes_a, axes_b = self._get_axes_lists()
        m = math.prod(a.shape[i] for i in axes_a)
        n = math.prod(b.shape[i] for i in axes_b)

        num_out = (a.size // m) * (b.size // n)
        return num_out * (2 * m - 1)


class _bitwise_and(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(np.bitwise_and(a.data, b.data))
        return self.result, partial(self.__grad__, lib_=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.bitwise_and(a.data, b.data))
        return self.result, partial(self.__grad__, lib_=mx)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)


class _bitwise_or(operation):
    def __init__(self) -> None:
        super().__init__()

    @binary_func_op(has_gradient=False)
    def cpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(np.bitwise_or(a.data, b.data))
        return self.result, partial(self.__grad__, lib_=np)

    @binary_func_op(has_gradient=False, device="gpu")
    def gpu(self, a: Tensor, b: Tensor) -> _FuncOpReturnType:
        self.result = Tensor(mx.bitwise_or(a.data, b.data))
        return self.result, partial(self.__grad__, lib_=mx)

    def __grad__(self, lib_: ModuleType) -> _GradFuncType:
        return lib_.array(0.0), lib_.array(0.0)
