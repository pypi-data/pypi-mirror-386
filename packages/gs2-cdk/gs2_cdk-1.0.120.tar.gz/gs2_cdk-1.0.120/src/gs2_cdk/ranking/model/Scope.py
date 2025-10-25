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
from .options.ScopeOptions import ScopeOptions


class Scope:
    name: str
    target_days: int

    def __init__(
        self,
        name: str,
        target_days: int,
        options: Optional[ScopeOptions] = ScopeOptions(),
    ):
        self.name = name
        self.target_days = target_days

    def properties(
        self,
    ) -> Dict[str, Any]:
        properties: Dict[str, Any] = {}

        if self.name is not None:
            properties["name"] = self.name
        if self.target_days is not None:
            properties["targetDays"] = self.target_days

        return properties
