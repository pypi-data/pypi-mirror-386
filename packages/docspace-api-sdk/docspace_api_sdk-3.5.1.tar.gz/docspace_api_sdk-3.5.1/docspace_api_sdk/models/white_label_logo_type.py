#
# (c) Copyright Ascensio System SIA 2025
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
#



from __future__ import annotations
import json
from enum import Enum
from typing_extensions import Self


class WhiteLabelLogoType(int, Enum):
    """
    WhiteLabelLogoType
    """

    """
    allowed enum values
    """
    NUMBER_1 = 1
    NUMBER_2 = 2
    NUMBER_3 = 3
    NUMBER_4 = 4
    NUMBER_5 = 5
    NUMBER_6 = 6
    NUMBER_7 = 7
    NUMBER_8 = 8
    NUMBER_9 = 9
    NUMBER_10 = 10
    NUMBER_11 = 11
    NUMBER_12 = 12
    NUMBER_13 = 13
    NUMBER_14 = 14
    NUMBER_15 = 15
    NUMBER_16 = 16

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of WhiteLabelLogoType from a JSON string"""
        return cls(json.loads(json_str))


