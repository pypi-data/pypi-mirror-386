# Copyright 2016- Game Server Services, Inc. or its affiliates. All Rights
# Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.
from __future__ import annotations
from typing import *
from .options.DistributeResourceOptions import DistributeResourceOptions


class DistributeResource:
    action: str
    request: str

    def __init__(
        self,
        action: str,
        request: str,
        options: Optional[DistributeResourceOptions] = DistributeResourceOptions(),
    ):
        self.action = action
        self.request = request

    def properties(
        self,
    ) -> Dict[str, Any]:
        properties: Dict[str, Any] = {}

        if self.action is not None:
            properties["action"] = self.action.value
        if self.request is not None:
            properties["request"] = self.request

        return properties
