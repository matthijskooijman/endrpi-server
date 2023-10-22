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
from endrpi.model.led import LedState

from .pixelbuf import PixelBuf


target_freq = 800000
reset_period = 50e-6
bits_per_period = 3


def write_leds(bus: int, dev: int, state: LedState) -> ActionResult[MessageData]:
    class SpiPixelBuf(PixelBuf):
        def _transmit(self, buffer):
            spi = spidev.SpiDev()
            spi.open(bus, dev)
            spi.mode = 3
            spi.max_speed_hz = int(bits_per_period * target_freq)

            try:
                spi.no_cs = True
            except OSError as e:
                import errno
                if e.errno == errno.EINVAL:
                    get_logger().warn(f'SPI_NO_CS not supported, continuing without setting it')
                else:
                    raise

            # Start with a low period to ensure the first transition is low-to-high
            output = BitArray('0b00000000')
            # Add a reset period before starting, to get a clean start on SPI
            # controllers that let MOSI idle high instead of low. On those
            # controllers, this causes a short blink (the leds latch in zero
            # values before receiving the actual values), but without this, it
            # seems the leds input state machine gets confused and you get
            # seemingly random (but reproducible) output.

            output += Bits(length=int(reset_period * target_freq * bits_per_period * 1.1))

            for byte in buffer:
                # print(byte)
                for bit in Bits(uint=byte, length=8):
                    assert bits_per_period == 3
                    # print(bit)
                    if bit:
                        output += '0b110'
                    else:
                        output += '0b100'

            # Reset period to terminate transmission
            output += Bits(length=int(reset_period * target_freq * bits_per_period * 1.1))

            # print(output.bin)

            spi.xfer(output.tobytes())
            spi.close()

    byteorder = "BGR"
    brightness = state.brightness
    buf = SpiPixelBuf(len(state.values), byteorder=byteorder, brightness=brightness)
    for idx, pixel in enumerate(state.values):
        buf[idx] = pixel
    buf.show()

    # TODO: Handle errors (e.g. unknown SPI dev)?
    return success_action_result("OK")
