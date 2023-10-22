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

from fastapi import APIRouter, status

from endrpi.actions.led import write_leds
from endrpi.model.message import MessageData
from endrpi.model.led import LedState
from endrpi.utils.api import http_response

# Router that is exported to the server
router = APIRouter()


@router.put(
    '/leds/{bus}/{dev}',
    description='Write colors to addressable leds connected to the MOSI pin of the given SPI bus (actual device does not matter, since CS is not used, but it must exist). Values can either be 0xRRGGBB integers, or [R, G, B] lists.',
    responses={
        status.HTTP_200_OK: {
            'model': MessageData
        },
    }
)
async def put_leds(bus: int, dev: int, led_state: LedState):
    # TODO: Handle errors (uknown bus?)
    action_result = write_leds(bus, dev, led_state)
    return http_response(action_result)
