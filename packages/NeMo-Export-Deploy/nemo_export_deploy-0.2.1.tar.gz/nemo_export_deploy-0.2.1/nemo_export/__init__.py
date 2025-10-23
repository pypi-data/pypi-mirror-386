# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
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

# WAR for trtllm and lightning conflict
from nemo_export_deploy_common.package_info import __package_name__, __version__

try:
    from nemo.lightning import io

    HAVE_IO = True
except (ImportError, ModuleNotFoundError):
    HAVE_IO = False

__all__ = ["__version__", "__package_name__"]

if HAVE_IO:
    __all__ += ["io"]
