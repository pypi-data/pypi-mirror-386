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
from .SlotModel import SlotModel
from .options.PropertyFormModelOptions import PropertyFormModelOptions


class PropertyFormModel:
    name: str
    slots: List[SlotModel]
    metadata: Optional[str] = None

    def __init__(
        self,
        name: str,
        slots: List[SlotModel],
        options: Optional[PropertyFormModelOptions] = PropertyFormModelOptions(),
    ):
        self.name = name
        self.slots = slots
        self.metadata = options.metadata if options.metadata else None

    def properties(
        self,
    ) -> Dict[str, Any]:
        properties: Dict[str, Any] = {}

        if self.name is not None:
            properties["name"] = self.name
        if self.metadata is not None:
            properties["metadata"] = self.metadata
        if self.slots is not None:
            properties["slots"] = [
                v.properties(
                )
                for v in self.slots
            ]

        return properties
