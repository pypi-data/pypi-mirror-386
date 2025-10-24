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
"""Mosaic-GPU utils."""

import jax
from jax.extend import backend
from tokamax._src import config as config_lib


def has_mosaic_gpu_support(device: jax.Device | None = None) -> bool:
  if config_lib.cross_compile.value:
    return True
  if device is None:
    device = backend.get_default_device()

  if device.platform != 'gpu':
    return False

  # Only currently supported for Hopper and above.
  return float(device.compute_capability) >= 9.0
