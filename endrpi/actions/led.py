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

from bitstring import Bits, BitArray
from typing import List
import spidev

from endrpi.config.logging import get_logger
from endrpi.model.action_result import ActionResult, success_action_result
from endrpi.model.message import MessageData
from endrpi.model.led import LedState, Protocol

from .pixelbuf import PixelBuf


def write_leds(bus: int, dev: int, state: LedState) -> ActionResult[MessageData]:
    if state.protocol == Protocol.WS2812B:
        # Period is 1/800khz = 1250us, one bit is 416us
        target_freq = 800000
        reset_period = 50e-6
        bit_patterns = ('0b100', '0b110')
        bits_per_period = 3
        byteorder = state.byteorder or "BGR"
    elif state.protocol == Protocol.WS2811:
        # High speed version (800khz)
        # Period is 1/800khz = 1250us, one bit is 312us
        target_freq = 800000
        reset_period = 280e-6
        bit_patterns = ('0b1000', '0b1100')
        bits_per_period = 4
        byteorder = state.byteorder or "RGB"
    elif state.protocol == Protocol.WS2815:
        # WS2815
        # Period is 1/800khz = 1250us, one bit is 312us
        target_freq = 800000
        reset_period = 280e-6
        bit_patterns = ('0b1000', '0b1110')
        bits_per_period = 4
        byteorder = state.byteorder or "RGB"
    else:
        raise Exception("Unknown protocol")

    class SpiPixelBuf(PixelBuf):
        def _transmit(self, buffer):
            spi = spidev.SpiDev()
            spi.open(bus, dev)
            spi.mode = 3
            spi.max_speed_hz = int(bits_per_period * target_freq)

            output = BitArray()
            for byte in buffer:
                # print(byte)
                for bit in Bits(uint=byte, length=8):
                    # print(bit)
                    output += bit_patterns[int(bit)]

            # Reset period to terminate transmission
            output += Bits(length=int(reset_period * target_freq * bits_per_period * 1.1))

            # print(output.bin)

            spi.xfer(output.tobytes())
            spi.close()

    brightness = state.brightness
    buf = SpiPixelBuf(len(state.values), byteorder=byteorder, brightness=brightness)
    for idx, pixel in enumerate(state.values):
        buf[idx] = pixel
    buf.show()

    # TODO: Handle errors (e.g. unknown SPI dev)?
    return success_action_result("OK")
