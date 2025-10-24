# Copyright 2025 Emcie Co Ltd.
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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, TypeAlias
from typing_extensions import override


ModerationTag: TypeAlias = Literal[
    "jailbreak",
    "harassment",
    "hate",
    "illicit",
    "self-harm",
    "sexual",
    "violence",
]


@dataclass(frozen=True)
class ModerationCheck:
    flagged: bool
    tags: list[ModerationTag]


class ModerationService(ABC):
    @abstractmethod
    async def check(
        self,
        content: str,
    ) -> ModerationCheck: ...


class NoModeration(ModerationService):
    @override
    async def check(
        self,
        content: str,
    ) -> ModerationCheck:
        return ModerationCheck(flagged=False, tags=[])
