#  Copyright (c) 2023 Matthijs Kooijman
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from typing import List, Union

from pydantic import BaseModel, Field


class LedState(BaseModel):
    values: List[Union[int, List[int]]] = Field(examples = [
        # TODO: These examples are not rendered by Swagger?
        # Split RGB values
        [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
        # RGB binary values (shown in decimal - JSON does not support hex literals)
        [16711680, 16711680, 255],
    ])
    brightness: float = Field(default = 1.0)
