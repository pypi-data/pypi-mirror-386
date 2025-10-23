# Copyright The Caikit Authors
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
"""
Typing constant for the Runtime Context

While caikit.core is not directly knowledgeable of caikit.interfaces or
caikit.runtime, there are several functions within the core that expose the
option to optionally handle context information when being called inside of a
runtime request handler. This forward-declaration allows those methods to use a
consistent type that derived classes would use directly.
"""
# Standard
from typing import Union

RuntimeServerContextType = Union[
    "grpc.ServicerContext", "fastapi.Request"  # noqa: F821
]
