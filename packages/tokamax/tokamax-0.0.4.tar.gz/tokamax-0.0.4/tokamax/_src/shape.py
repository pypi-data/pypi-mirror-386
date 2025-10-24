# Copyright 2025 DeepMind Technologies Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Shape utilities."""

import functools
import sys
from typing import Any, TypeAlias
from unittest import mock

from einshape.src.jax import jax_ops as einshape_jax
import jax
from jax import export
from jax.experimental import pallas as pl
import jax.numpy as jnp


PyTree = Any
SymbolicDim: TypeAlias = type(export.symbolic_shape("_a")[0])  # pytype: disable=invalid-annotation

einshape = lambda eq, **kw: functools.partial(einshape_jax.einshape, eq, **kw)


def pad_dim_to(x: jax.Array, n: int, axis: int) -> jax.Array:
  """Pads `x` to size `n` along `axis`."""
  if (padding := n - x.shape[axis]) == 0:
    return x
  if padding < 0:
    raise ValueError(f"Cannot pad {x.shape[axis]} to smaller size {n}")
  pad_width = [(0, 0)] * x.ndim
  pad_width[axis] = (0, padding)
  return jnp.pad(x, pad_width)


def pad_to_next_multiple_of(x: jax.Array, m: int, axis: int = 0) -> jax.Array:
  """Pads `x` to the next multiple of `m` along `axis`."""
  return pad_dim_to(x, pl.cdiv(x.shape[axis], m) * m, axis)


def upcast_broadcast():
  """Returns context manager forcing upcast before `jax.lax.broadcast_in_dim`.

  Upcasting the broadcast input ensures that the VJP reduction will occur in the
  higher precision, improving accuracy for gradients of broadcast values.
  """

  @functools.wraps(jax.lax.broadcast_in_dim)
  def broadcast_in_dim(x, *args, **kwargs):
    orig_dtype = x.dtype
    if jnp.issubdtype(x.dtype, jnp.floating):
      # Upcast to at least f32 before broadcast, so VJP reduction is in f32.
      x = x.astype(jnp.promote_types(x.dtype, jnp.float32))
    return jax.lax.broadcast_in_dim(x, *args, **kwargs).astype(orig_dtype)

  # Ugly hack, reaching into JAX internals.
  lax = sys.modules["jax._src.lax.lax"]
  return mock.patch.object(lax, "broadcast_in_dim", broadcast_in_dim)


def contains_symbolic_shape(args: PyTree) -> bool:
  """Returns whether the given PyTree contains symbolic shapes."""

  args = jax.tree.leaves(args)
  for x in args:
    # This could match a variety of types, such as jax.ShapeDtypeStruct,
    # JitTracer, GradTracer, etc.
    if hasattr(x, "shape") and isinstance(x.shape, tuple):
      for s in x.shape:
        if isinstance(s, SymbolicDim):
          return True
  return False
