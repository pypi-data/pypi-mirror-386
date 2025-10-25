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
#
# deny overwrite
from __future__ import annotations
from typing import *
from .options.AttachSecurityPolicyOptions import AttachSecurityPolicyOptions
from ...core import CdkResource, Stack


class AttachSecurityPolicy(CdkResource):

    stack: Stack
    user_name: str
    security_policy_id: str

    def __init__(
        self,
        stack: Stack,
        user_name: str,
        security_policy_id: str,
        resource_name: str = None,
    ):
        self.stack = stack
        self.user_name = user_name
        self.security_policy_id = security_policy_id
        if resource_name is None:
            resource_name = self.default_resource_name()

        super().__init__(resource_name)
        stack.add_resource(self)

    def alternate_keys(self):
        return self.user_name

    def resource_type(self) -> str:
        return "GS2::Identifier::AttachSecurityPolicy"

    def properties(self) -> Dict[str, Any]:
        return {
            "userName": self.user_name,
            "securityPolicyId": self.security_policy_id,
        }
