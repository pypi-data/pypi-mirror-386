# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import logging
import shutil
from dataclasses import dataclass

import torch
import torch.distributed.checkpoint as dcp
from torch.distributed.checkpoint.metadata import Metadata as DcpMeta
from torchstore.transport.buffers import rdma_available

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

KEY_DELIM = "."
DCP_WHOLE_STATE_TAG = "dcp_whole_state_dict"


@dataclass
class DcpHandle:
    checkpoint_id: str | None = None
    metadata: DcpMeta | None = None
    param_names: list[str] | None = None

    def drop(self) -> None:
        if self.checkpoint_id is None:
            raise ValueError("Dropping a null DcpHandle")
        if self.checkpoint_id.startswith("manifold://"):
            # Probably don't need to delete the checkpoint if it's on manifold
            logger.warning(
                f"Skipping deletion of {self.checkpoint_id} since it's on manifold"
            )
            self.checkpoint_id = None
            self.metadata = None
            self.param_names = None
            return

        try:
            shutil.rmtree(self.checkpoint_id, ignore_errors=False)
            logger.debug(f"Removed old weights at {self.checkpoint_id}")
        except OSError as e:
            logger.error(f"Error deleting {self.checkpoint_id}: {e}")
        finally:
            self.checkpoint_id = None
            self.metadata = None
            self.param_names = None


def load_tensor_from_dcp(handle: DcpHandle, param_name) -> torch.Tensor:
    tensor_meta = handle.metadata.state_dict_metadata[param_name]
    buffer = torch.empty(tensor_meta.size, dtype=tensor_meta.properties.dtype)
    dcp.load(checkpoint_id=handle.checkpoint_id, state_dict={param_name: buffer})
    return buffer


def get_param_prefix(policy_version: int) -> str:
    return f"policy_ver_{policy_version:010d}"


def get_param_key(policy_version: int, name: str) -> str:
    return f"policy_ver_{policy_version:010d}{KEY_DELIM}{name}"


def extract_param_name(key: str) -> str:
    return KEY_DELIM.join(key.split(KEY_DELIM)[1:])


def get_dcp_whole_state_dict_key(policy_version: int) -> str:
    return f"{get_param_prefix(policy_version)}{KEY_DELIM}{DCP_WHOLE_STATE_TAG}"


def rdma_enabled() -> bool:
    """Return if TorchStore thinks we're using RDMA"""
    return rdma_available()
