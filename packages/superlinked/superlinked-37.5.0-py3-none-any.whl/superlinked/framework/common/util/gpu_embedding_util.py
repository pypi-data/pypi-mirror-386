# Copyright 2024 Superlinked, Inc.
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

import torch

from superlinked.framework.common.settings import settings

CPU_DEVICE_TYPE = "cpu"
CUDA_DEVICE_TYPE = "cuda"
MPS_DEVICE_TYPE = "mps"


class GpuEmbeddingUtil:
    @classmethod
    def get_device(cls) -> str:
        if torch.cuda.is_available():
            return CUDA_DEVICE_TYPE
        if settings.ENABLE_MPS and torch.backends.mps.is_available():
            return MPS_DEVICE_TYPE
        return CPU_DEVICE_TYPE
