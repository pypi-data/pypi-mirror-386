import lucid
import lucid.nn as nn
from lucid._tensor import Tensor

from lucid.types import _ShapeLike


def normalize(
    input_: Tensor, ord: int = 2, axis: int = 1, eps: float = 1e-12
) -> Tensor:
    norm = lucid.sum(lucid.abs(input_) ** ord, axis=axis, keepdims=True) ** (1 / ord)
    norm = lucid.maximum(norm, lucid.tensor(eps))

    return input_ / norm


def batch_norm(
    input_: Tensor,
    running_mean: Tensor | None,
    running_var: Tensor | None,
    weight: Tensor | None = None,
    bias: Tensor | None = None,
    training: bool = True,
    momentum: float = 0.1,
    eps: float = 1e-5,
) -> Tensor:
    C = input_.shape[1]
    spatial_dim = input_.ndim - 2

    use_batch_stats = training or running_mean is None or running_var is None

    if use_batch_stats:
        batch_mean = input_.mean(axis=(0, *range(2, input_.ndim)), keepdims=True)
        batch_var = input_.var(axis=(0, *range(2, input_.ndim)), keepdims=True)

        if running_mean is not None and running_var is not None:
            running_stats_ = (
                momentum * batch_mean.flatten() + (1 - momentum) * running_mean,
                momentum * batch_var.flatten() + (1 - momentum) * running_var,
            )

            if isinstance(running_mean, nn.Buffer) and isinstance(
                running_var, nn.Buffer
            ):
                running_mean.data = running_stats_[0].data
                running_var.data = running_stats_[1].data
            else:
                running_mean, running_var = running_stats_

        mean = batch_mean
        var = batch_var
    else:
        mean = running_mean.reshape(1, C, *(1,) * spatial_dim)
        var = running_var.reshape(1, C, *(1,) * spatial_dim)

    normalized = (input_ - mean) / lucid.sqrt(var + eps)

    if weight is not None:
        weight = weight.reshape((1, C) + (1,) * spatial_dim)
        normalized *= weight

    if bias is not None:
        bias = bias.reshape((1, C) + (1,) * spatial_dim)
        normalized += bias

    return normalized


def layer_norm(
    input_: Tensor,
    normalized_shape: _ShapeLike,
    weight: Tensor | None = None,
    bias: Tensor | None = None,
    eps: float = 1e-5,
) -> Tensor:
    if input_.shape[-len(normalized_shape) :] != normalized_shape:
        raise ValueError(
            "Input tensor's normalized shape must match "
            + "the provided `normalized_shape`."
        )

    mean = input_.mean(axis=tuple(range(-len(normalized_shape), 0)), keepdims=True)
    var = input_.var(axis=tuple(range(-len(normalized_shape), 0)), keepdims=True)

    normalized = (input_ - mean) / lucid.sqrt(var + eps)
    if weight is not None:
        normalized *= weight.reshape(
            (1,) * (input_.ndim - len(normalized_shape)) + normalized_shape
        )
    if bias is not None:
        normalized += bias.reshape(
            (1,) * (input_.ndim - len(normalized_shape)) + normalized_shape
        )

    return normalized


def instance_norm(
    input_: Tensor,
    running_mean: Tensor | None,
    running_var: Tensor | None,
    weight: Tensor | None = None,
    bias: Tensor | None = None,
    training: bool = True,
    momentum: float = 0.1,
    eps: float = 1e-5,
) -> Tensor:
    C = input_.shape[1]
    spatial_dims = input_.shape[2:]

    if training:
        axes = tuple(range(2, input_.ndim))
        instance_mean = input_.mean(axis=axes, keepdims=True)
        instance_var = input_.var(axis=axes, keepdims=True)

        if running_mean is not None and running_var is not None:
            running_stats_ = (
                momentum * instance_mean.mean(axis=0).flatten()
                + (1 - momentum) * running_mean,
                momentum * instance_var.mean(axis=0).flatten()
                + (1 - momentum) * running_var,
            )

            if isinstance(running_mean, nn.Buffer) and isinstance(
                running_var, nn.Buffer
            ):
                running_mean.data = running_stats_[0].data
                running_var.data = running_stats_[1].data
            else:
                running_mean, running_var = running_stats_

        mean = instance_mean
        var = instance_var
    else:
        mean = running_mean.reshape(1, C, *(1,) * len(spatial_dims))
        var = running_var.reshape(1, C, *(1,) * len(spatial_dims))

    normalized = (input_ - mean) / lucid.sqrt(var + eps)

    if weight is not None:
        weight = weight.reshape((1, C) + (1,) * len(spatial_dims))
        normalized *= weight

    if bias is not None:
        bias = bias.reshape((1, C) + (1,) * len(spatial_dims))
        normalized += bias

    return normalized


def group_norm(
    input_: Tensor,
    num_groups: int,
    weight: Tensor | None,
    bias: Tensor | None,
    eps: float = 1e-5,
) -> Tensor:
    N, C, *spatial_dims = input_.shape
    assert C % num_groups == 0, "Number of channels must be divisible by num_groups"

    group_size = C // num_groups
    new_shape = (N, num_groups, group_size, *spatial_dims)
    reshaped = input_.reshape(*new_shape)

    axes = (2,) + tuple(range(3, reshaped.ndim))
    mean = reshaped.mean(axis=axes, keepdims=True)
    var = reshaped.var(axis=axes, keepdims=True)

    normalized = (reshaped - mean) / lucid.sqrt(var + eps)
    normalized = normalized.reshape(N, C, *spatial_dims)

    if weight is not None:
        weight = weight.reshape(1, C, *(1,) * len(spatial_dims))
        normalized *= weight

    if bias is not None:
        bias = bias.reshape(1, C, *(1,) * len(spatial_dims))
        normalized += bias

    return normalized


def global_response_norm(
    input_: Tensor, gamma: Tensor, beta: Tensor, eps: float = 1e-6
) -> Tensor:
    Gx: Tensor = lucid.linalg.norm(input_, ord=2, axis=(-1, -2), keepdims=True)
    Nx = Gx / (Gx.mean(axis=-1, keepdims=True) + eps)
    return gamma * (input_ * Nx) + beta * input_
