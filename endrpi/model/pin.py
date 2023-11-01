#  Copyright (c) 2020 - 2021 Persanix LLC. All rights reserved.
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

from enum import Enum
from typing import Union, Dict, NamedTuple, Optional

from pydantic import BaseModel

class PinDescTuple(NamedTuple):
    chipnum: int
    linenum: int

class RaspberryPiPinIds(PinDescTuple, Enum):
    """Enumerations for pin ids on the Orange Pi 5."""
    GPIO1_B7 = PinDescTuple(1, 1 * 8 + 7)
    GPIO1_B6 = PinDescTuple(1, 1 * 8 + 6)
    GPIO1_C6 = PinDescTuple(1, 2 * 8 + 6)
    GPIO4_A3 = PinDescTuple(4, 0 * 8 + 3)
    GPIO4_A4 = PinDescTuple(4, 0 * 8 + 4)
    GPIO4_B2 = PinDescTuple(4, 1 * 8 + 2)
    GPIO0_D5 = PinDescTuple(0, 3 * 8 + 5)
    GPIO4_B3 = PinDescTuple(4, 1 * 8 + 3)
    GPIO0_D4 = PinDescTuple(0, 3 * 8 + 4)
    GPIO1_D3 = PinDescTuple(1, 3 * 8 + 3)
    GPIO1_D2 = PinDescTuple(1, 3 * 8 + 2)
    GPIO1_C1 = PinDescTuple(1, 2 * 8 + 1)
    GPIO1_C0 = PinDescTuple(1, 2 * 8 + 0)
    GPIO1_C2 = PinDescTuple(1, 2 * 8 + 2)
    GPIO1_C4 = PinDescTuple(1, 2 * 8 + 4)
    GPIO1_A3 = PinDescTuple(1, 0 * 8 + 3)
    GPIO0_B6 = PinDescTuple(0, 1 * 8 + 6)
    GPIO0_B5 = PinDescTuple(0, 1 * 8 + 5)

    @classmethod
    def from_bcm_id(cls, pin_id: str) -> Union['RaspberryPiPinIds', None]:
        # Attempt to instantiate a raspberry pi pin id from a string and return the pin id
        try:
            return cls[pin_id]
        except KeyError:
            return None


class PinPull(str, Enum):
    """Enumerations for the pull states of a GPIO pin."""
    FLOATING = 'FLOATING'
    UP = 'UP'
    DOWN = 'DOWN'


class PinIo(str, Enum):
    """Enumerations for the io states of a GPIO pin."""
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'


class PinConfiguration(BaseModel):
    """Interface for GPIO pin io function, state, and pull."""
    io: PinIo
    state: Optional[float]
    pull: Optional[PinPull]


class PinEdges(str, Enum):
    """Enumerations for edges that can be watched on a GPIO pin."""
    BOTH = 'BOTH'
    RISING = 'RISING'
    FALLING = 'FALLING'


class PinDrivenState(BaseModel):
    """Interface for GPIO pin Driven status."""
    driven: bool


PinConfigurationMap = Dict[RaspberryPiPinIds, PinConfiguration]
