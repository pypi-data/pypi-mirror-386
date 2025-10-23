# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from .gpu_manager import get_gpu_ids, release_gpus

__all__ = [
    "get_gpu_ids",
    "release_gpus",
]
