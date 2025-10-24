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

"""Mini-mask creation library."""
from __future__ import annotations

import collections
import functools
from typing import Any, NamedTuple

import jax
import jax.lax as lax
import jax.numpy as jnp
import numpy as np
from tokamax._src.ops.experimental.tpu.splash_attention import splash_attention_mask as mask_lib

# mypy: ignore-errors

MaskCallable = Any


def find_bounds(
    arr: jax.Array | np.ndarray,
) -> tuple[jax.Array | np.ndarray | None, jax.Array | np.ndarray | None]:
  # Find the first and last block of a row to determine when to initialize/store
  # the output.

  if arr is None:
    return None, None

  bounds_start = (arr != jnp.roll(arr, shift=1, axis=-1)).astype(jnp.int32)
  bounds_end = (arr != jnp.roll(arr, shift=-1, axis=-1)).astype(jnp.int32)
  bounds_start = bounds_start.at[0].set(1)
  bounds_end = bounds_end.at[-1].set(1)

  return bounds_start, bounds_end


# Logic for processing NumPy masks for kernels
class MaskInfo(NamedTuple):
  """Contains runtime masking information for the Splash attention kernel.

  The arrays, mask_next and block_mask are placed in TPU
  scalar-memory. This is a scarse resource so the mask creation logic attempts
  to shrink the data-type of these arrays to the smallest possible one.
  This can be: np.int32, np.int16 or np.int8.

  Attributes:
    mask_next: An integer[num_active_blocks] NumPy array where each
      entry contains the next mask block index in `partial_mask_blocks` to
      prefetch.
    active_rows: An integer[num_active_blocks] NumPy array where each entry
      contains the row index of the corresponding active block in the original
      mask.
    active_cols: An integer[num_active_blocks] NumPy array where each entry
      contains the column index of the corresponding active block in the
      original mask.
    block_mask: An integer[num_active_blocks] NumPy array where each entry is
      either 1 or 2. 1 means the corresponding block is full and 2 means the
      corresponding block is partially masked.
    num_active_blocks: An integer[] NumPy array whose
      entries are the sizes of the corresponding blocks in the original mask.
    partial_mask_blocks: An int8[num_partial_blocks, block_q, block_kv] NumPy
      array that contains the blocks of the original mask that contained both
      zeros and ones. The entries in `mask_next` point to indices in the first
      axis of this array.
    q_sequence: A i32[q_sequence_length] NumPy array. When using causal masking,
      this contains the list of indices that correspond to q tokens. For plain
      causal this is just np.arange(q_sequence_length).
  """

  mask_next: np.ndarray | jax.Array | None
  active_rows: np.ndarray | jax.Array | None
  active_cols: np.ndarray | jax.Array | None
  block_mask: np.ndarray | jax.Array | None
  num_active_blocks: np.ndarray | jax.Array | None
  partial_mask_blocks: np.ndarray | jax.Array | None
  q_sequence: np.ndarray | None


def _downcast_to_small_type(array: np.ndarray) -> np.ndarray:
  """Downcast numpy array.

  If possible, downcast the data-type of the input array to the smallest numpy
  type (among np.int16 and np.int8) that fits the content of the array.

  Args:
    array: the array to downcast

  Returns:
    The downcasted array.

  Raises:
    ValueError: if the input array is not np.int32 or if its elements are not
    all positive.
  """
  if array.dtype != np.int32:
    raise ValueError(f'Expected int32 input, but got {array.dtype}.')

  if not np.all(array >= 0):
    raise ValueError('Expected non-negative array.')

  if array.size == 0:
    return array

  max_value = np.max(array)

  if max_value <= np.iinfo(np.int8).max:
    return array.astype(np.int8)
  elif max_value <= np.iinfo(np.int16).max:
    return array.astype(np.int16)
  else:
    return array.astype(np.int32)


def _check_mask(mask: mask_lib.Mask) -> None:
  """Check that the given mask is valid.

  A row of all zeros along the kv dimension would result in a division by zero
  when computing the softmax. This function is meant to protect against that
  case.

  Args:
    mask: the mask to check.

  Raises:
    ValueError: the mask is invalid.
  """

  assert len(mask.shape) == 2

  exception_message = (
      'Some rows of the mask (along the kv dimension) are all zeros.\nThis is'
      ' would result in a division by zero when computing the attention'
      ' softmax.'
  )

  is_row_non_zero = np.zeros(mask.shape[0], dtype=np.bool_)
  for col in range(mask.shape[1]):
    # Mask only supports slice indices.
    is_row_non_zero = np.logical_or(
        is_row_non_zero,
        mask[(slice(0, mask.shape[0]), slice(col, col + 1))][:, 0],
    )
  if not is_row_non_zero.all():
    raise ValueError(exception_message)


class _HashableNDArray:
  """Helper to make a numpy array hashable: can be added associative containers.

  Attributes:
    array: The underlying numpy array.
  """
  array: np.ndarray

  def __init__(self, array: np.ndarray):
    self.array = array

  def __hash__(self):
    return hash(self.array.tobytes())

  def __eq__(self, other: object) -> bool:
    if not isinstance(other, _HashableNDArray):
      return NotImplemented
    return np.array_equal(self.array, other.array, equal_nan=True)


def _get_mask_info(
    mask: mask_lib.Mask | jax.Array,
    block_shape: tuple[int, int],
    coords_to_partial_mask_block_index: dict[tuple[int, int], int],
    q_seq_start: int,
    q_seq_shard_size: int,
    blocked_q_seq_start: int,
    is_dkv: bool,
    return_dynamic_grid: bool,
):
  """Process a slice of the mask to compute mask_next.

  Args:
    mask: The full mask to be sliced according to the sequence ranges
    block_shape: Shape of the Pallas grid block.
    coords_to_partial_mask_block_index: Mapping between the pallas launch grid
      coordinates and the index of the corresponding block in partial mask block
      list.
    q_seq_start: Start index along the Q sequence for the current shard (in
      number of tokens).
    q_seq_shard_size: Number of tokens along the Q sequence for the current
      shard.
    blocked_q_seq_start: Start index along the Q sequence for the current shard
      (in number of grid blocks)
    is_dkv: True if we are processing the dKV mask
    return_dynamic_grid: If True, the grid is dynamic and the function returns
      only the active blocks. Otherwise, the kernel grid covers the entire mask.
  Returns:
    Slice of mask_next (if required) that correspond to the current mask slice.
  """
  _, kv_seq_len = mask.shape
  q_block_size, kv_block_size = block_shape

  q_block_count, q_mod = divmod(q_seq_shard_size, q_block_size)
  kv_block_count, kv_mod = divmod(kv_seq_len, kv_block_size)
  total_blocks = q_block_count * kv_block_count

  assert q_mod == 0
  assert kv_mod == 0

  blocked_shape = (
      (kv_block_count, q_block_count)
      if is_dkv
      else (q_block_count, kv_block_count)
  )
  active_coords = []
  partial_blocks = {}
  block_mask = np.zeros(blocked_shape, dtype=jnp.int32)
  for idx in np.ndindex(blocked_shape):
    if is_dkv:
      kv_idx, q_idx = idx
    else:
      q_idx, kv_idx = idx
    chunk = mask[(
        slice(
            q_seq_start + q_idx * q_block_size,
            q_seq_start + (q_idx + 1) * q_block_size,
        ),
        slice(kv_idx * kv_block_size, (kv_idx + 1) * kv_block_size),
    )]
    if chunk.any():
      active_coords.append(idx)
      if not chunk.all():
        block_mask[idx] = 1
        coord_global = (q_idx + blocked_q_seq_start, kv_idx)
        partial_blocks[idx] = coords_to_partial_mask_block_index[coord_global]
      else:
        block_mask[idx] = 2

  active_rows, active_cols, mask_next = [], [], []
  # If the mask is completely zero'd out return freshly initialized outputs.
  if not partial_blocks:
    return mask_next

  mask_coords_iter = iter(list(partial_blocks.keys()))
  first_m = coord_m = next(mask_coords_iter)

  for idx in np.ndindex(blocked_shape):
    if return_dynamic_grid and block_mask[idx] == 0:
      # Empty compute blocks need to processed in the backwards pass to
      # initialize outputs.
      continue

    is_next_mask = idx > coord_m
    if is_next_mask:
      try:
        coord_m = next(mask_coords_iter)  # type: ignore
      except StopIteration:
        coord_m = first_m

    active_rows.append(idx[0])
    active_cols.append(idx[1])
    mask_next.append(partial_blocks[coord_m])

  # TODO: resize all arrays to the maximum of grid sizes in each shard.
  flat_block_mask = block_mask.flatten()

  if return_dynamic_grid:
    flat_block_mask = flat_block_mask[flat_block_mask != 0]

  assert len(active_rows) == len(active_cols) == len(mask_next)
  grid_size = len(active_rows)

  pad_length = total_blocks - flat_block_mask.size
  active_rows = np.pad(np.array(active_rows, dtype=np.int32), (0, pad_length))
  active_cols = np.pad(np.array(active_cols, dtype=np.int32), (0, pad_length))
  mask_next = np.pad(np.array(mask_next, dtype=np.int32), (0, pad_length))
  flat_block_mask = np.pad(
      np.array(flat_block_mask, dtype=np.int32), (0, pad_length)
  )
  return active_rows, active_cols, mask_next, flat_block_mask, grid_size


def _process_dynamic_mask(
    mask: jax.Array,
    block_shape: tuple[int, int],
    is_dkv: bool,
    *,
    downcast_smem_data: bool = True,
    partial_mask_blocks_dtype: jnp.DTypeLike = np.int8,
) -> MaskInfo:
  """Process a dynamic mask to compute it's local sparsity data.

  Note that this operates on a single shard of the mask.

  Args:
    mask: [q_seq_len, kv_seq_len] jax.Array representing a dense mask to
      process.
    block_shape: A Tuple[int, int] representing the shape of the Pallas grid
      block.
    is_dkv: True if we are processing the dKV mask
    downcast_smem_data: If True, downcast the scalar-memory data of MaskInfo to
      a data type smaller than np.int32 (if possible).

  Returns:
    `MaskInfo`, a sparse representation of the dense mask.

  Raises:
    ValueError: if the input mask is invalid or the block sizes are not
    compatible with the mask sizes.
  """
  # TODO: Fix dynamic mask processing with the new sparsity format.
  raise NotImplementedError("Dynamic masks not supported.")

  if len(mask.shape) != 2:
    raise ValueError(f'Expected a 2-dim mask, instead got: {mask.shape}.')

  if mask.dtype != jnp.bool:
    raise ValueError(f'Expected a bool mask, instead got: {mask.dtype}.')

  q_seq_len, kv_seq_len = mask.shape
  q_block_size, kv_block_size = block_shape
  q_blocks_count, q_mod = divmod(q_seq_len, q_block_size)
  kv_blocks_count, kv_mod = divmod(kv_seq_len, kv_block_size)

  if q_mod != 0:
    raise ValueError(f'{q_block_size=} should divide {q_seq_len=}.')
  if kv_mod != 0:
    raise ValueError(f'{kv_block_size=} should divide {kv_seq_len=}.')

  # Tile the last 2 dimensions of the mask into 2D tiles of size `block_shape`.
  partial_mask_blocks = (
      mask.reshape(
          q_blocks_count,
          q_block_size,
          kv_blocks_count,
          kv_block_size,
      )
      .swapaxes(-2, -3)
      .astype(partial_mask_blocks_dtype)
  )

  # The block mask is 2 for all blocks with all entries set to True and 1 for
  # blocks with a mix of True and False entries.
  is_full_mask = jnp.all(partial_mask_blocks, axis=(-1, -2))
  is_empty_mask = jnp.logical_not(jnp.any(partial_mask_blocks, axis=(-1, -2)))
  block_mask = (1 + is_full_mask - is_empty_mask).astype(jnp.int32)

  mask_next = jnp.arange(
      q_blocks_count * kv_blocks_count, dtype=np.int32
  ).reshape(q_blocks_count, kv_blocks_count)
  mask_next = jnp.where(block_mask == 1, mask_next, 0)

  if is_dkv:
    partial_mask_blocks = partial_mask_blocks.mT

  def _downcast(array: jax.Array, max_value: int) -> jax.Array:
    if array.size == 0:
      return array

    if array.dtype != np.int32:
      raise ValueError(f'Expected int32 input, but got {array.dtype}.')

    if max_value <= np.iinfo(np.int8).max:
      return array.astype(np.int8)
    elif max_value <= np.iinfo(np.int16).max:
      return array.astype(np.int16)
    else:
      return array.astype(np.int32)

  if downcast_smem_data:
    block_mask = block_mask.astype(np.int8)  # values are in the range [0, 1, 2]
    mask_next = _downcast(
        mask_next, q_blocks_count * kv_blocks_count
    )

  # Collapsing because the block ids are linearized.
  partial_mask_blocks = lax.collapse(partial_mask_blocks, 0, 2)

  return MaskInfo(
      mask_next=mask_next,
      active_rows=None,
      active_cols=None,
      block_mask=None,
      num_active_blocks=None,
      partial_mask_blocks=partial_mask_blocks,
      q_sequence=None,
  )


# When used in a transformer network with multiple layers, the SplashAttention
# kernel is created several times with the same mask. Cache MaskInfo to avoid
# blowing up compile times. Ideally the size of the cache should be determined
# by the client.
@functools.lru_cache(maxsize=12)
def _process_mask(
    mask: mask_lib.Mask,  # [q_seq_len, kv_seq_len]
    block_shape: tuple[int, int],
    is_dkv: bool,
    *,
    downcast_smem_data: bool = True,
    partial_mask_blocks_dtype: jnp.DTypeLike = np.int8,
    q_seq_shards: int = 1,
    return_dynamic_grid: bool = True,
) -> tuple[MaskInfo, MaskCallable | None]:
  """Transform a dense mask into a sparse representation.

  The number Q sequence shards are needed to create a MaskInfo
  object that is partitionable (with shmap) along that dimension.
  Args:
    mask: Dense mask to process.
    block_shape: Shape of the Pallas grid block.
    is_dkv: True if we are processing the dKV mask
    downcast_smem_data: If True, downcast the SMEM data of MaskInfo to a data
      type smaller if possible.
    q_seq_shards: Number of Q sequence shards of the mesh in which the kernel is
      launched.

  Returns:
    `MaskInfo`, a sparse representation of the dense mask.
    `MaskCallable`: a callable that, given in input Q and KV indices, returns
      the value of the mask at those coordinates.

  Raises:
    ValueError: if the input mask is invalid or the block sizes are not
    compatible with the mask sizes.
  """

  if len(mask.shape) != 2:
    raise ValueError(f'Expected a 2-dim mask, instead got: {mask.shape=}')

  q_seq_len, kv_seq_len = mask.shape
  q_block_size, kv_block_size = block_shape
  q_blocks_count, q_mod = divmod(q_seq_len, q_block_size)
  kv_blocks_count, kv_mod = divmod(kv_seq_len, kv_block_size)

  if q_mod != 0:
    raise ValueError(f'{q_block_size=} should divide {q_seq_len=}.')
  if kv_mod != 0:
    raise ValueError(f'{kv_block_size=} should divide {kv_seq_len=}.')

  q_seq_len_per_shard, mod = divmod(q_seq_len, q_seq_shards)
  if mod != 0:
    raise ValueError(f'{q_seq_shards=} should divide {q_seq_len=}.')

  q_blocks_per_shard, mod = divmod(q_seq_len_per_shard, q_block_size)
  if mod != 0:
    raise ValueError(f'{q_block_size=} should divide {q_seq_len_per_shard=}.')

  # TODO: checking the validity of the masks is slow for large masks.
  # Disable it for now, reevaluate in the future.

  partial_mask_block_ids: dict[_HashableNDArray, int] = collections.defaultdict(
      lambda: len(partial_mask_block_ids)
  )
  coords_to_partial_mask_block_index: dict[tuple[int, int], int] = {}

  q_sequence = None
  mask_function = None

  # The mask object either define q_sequence and mask_function or none of
  # them.
  assert hasattr(mask, 'q_sequence') == hasattr(mask, 'mask_function')

  # If the mask object defines a q_sequence and a mask_function, then make use
  # of these in the kernel rather. This is preferable over loading the mask
  # from memory. When using a mask_function, then mask_next and
  # partial_mask_blocks are left undefined and not used in the kernel.
  if hasattr(mask, 'q_sequence') and hasattr(mask, 'mask_function'):
    q_sequence = mask.q_sequence
    mask_function = mask.mask_function

  # Identify the partial mask blocks and the value of the block mask for each
  # block.
  # Partial mask blocks are uniquified. When partitioning, all partial mask
  # blocks are replicated across shards.

  for coords in np.ndindex((q_blocks_count, kv_blocks_count)):
    (q_idx, kv_idx) = coords
    chunk = mask[(
        slice(q_idx * q_block_size, (q_idx + 1) * q_block_size),
        slice(kv_idx * kv_block_size, (kv_idx + 1) * kv_block_size),
    )]
    if chunk.any() and not chunk.all():
      partial_mask_block_id = partial_mask_block_ids[_HashableNDArray(chunk)]
      coords_to_partial_mask_block_index[coords] = partial_mask_block_id

  if not partial_mask_block_ids:
    num_active_blocks = None
    block_mask = None
    mask_next = None
    partial_mask_blocks = None
    active_rows = None
    active_cols = None
  else:
    partial_mask_blocks = [x.array for x in partial_mask_block_ids]
    partial_mask_blocks = np.stack(partial_mask_blocks, axis=0).astype(
        partial_mask_blocks_dtype
    )
    if is_dkv:
      partial_mask_blocks = np.swapaxes(partial_mask_blocks, -1, -2)

    # Work on a fraction of the mask at the time to compute the mask. This is
    # needed to compute the correct data indices, which are relative to the
    # current slice of the mask.

    q_seq_len_shard_size = q_blocks_per_shard * q_block_size

    (
        active_rows_slices,
        active_cols_slices,
        mask_next_slices,
        block_mask_slices,
        num_active_blocks,
    ) = zip(*[
        _get_mask_info(
            mask=mask,
            block_shape=block_shape,
            coords_to_partial_mask_block_index=coords_to_partial_mask_block_index,
            q_seq_start=shard_idx * q_seq_len_shard_size,
            q_seq_shard_size=q_seq_len_shard_size,
            blocked_q_seq_start=shard_idx * q_blocks_per_shard,
            is_dkv=is_dkv,
            return_dynamic_grid=return_dynamic_grid,
        )
        for shard_idx in range(q_seq_shards)
    ])

    # Concatenate the sequence shards.
    active_rows = np.concatenate(active_rows_slices, axis=0)
    active_cols = np.concatenate(active_cols_slices, axis=0)
    mask_next = np.concatenate(mask_next_slices, axis=0)
    block_mask = np.concatenate(block_mask_slices, axis=0)
    num_active_blocks = np.array(num_active_blocks, dtype=np.int32)

    if downcast_smem_data:
      mask_next = _downcast_to_small_type(mask_next)
      active_rows = _downcast_to_small_type(active_rows)
      active_cols = _downcast_to_small_type(active_cols)
      block_mask = _downcast_to_small_type(block_mask)

    if not return_dynamic_grid:
      active_rows = active_cols = None

  assert (mask_function is not None) == (q_sequence is not None)
  # When the mask can be computed inside the kernel with a mask_function,
  # there is no need to load it from memory. So mask_next and
  # partial_mask_blocks are unused.
  return (
      MaskInfo(
          mask_next=mask_next if mask_function is None else None,
          active_rows=active_rows,
          active_cols=active_cols,
          block_mask=block_mask,
          num_active_blocks=num_active_blocks,
          partial_mask_blocks=partial_mask_blocks
          if mask_function is None
          else None,
          q_sequence=q_sequence,
      ),
      mask_function,
  )


process_mask = functools.partial(_process_mask, is_dkv=False)
process_mask_dkv = functools.partial(_process_mask, is_dkv=True)

process_dynamic_mask = functools.partial(_process_dynamic_mask, is_dkv=False)
process_dynamic_mask_dkv = functools.partial(_process_dynamic_mask, is_dkv=True)
