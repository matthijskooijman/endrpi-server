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

from collections import defaultdict
from threading import Lock

from gpiozero import Device
from gpiozero.pins.local import LocalPiFactory
from gpiozero.pins.mock import MockFactory
from gpiozero.pins.native import NativeFactory
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero.exc import PinInvalidPin, PinSPIUnsupported

from endrpi.config.logging import get_logger
from endrpi.model.pin import RaspberryPiPinIds


class GenericInfo:
    """ Minimal (incomplete) implementation of PiBoardInfo to allow using gpios. """

    def to_gpio(self, spec):
        # Just accept raw (kernel gpio) pin numbers
        if isinstance(spec, int):
            return spec
        raise PinInvalidPin('{spec} is not a valid pin spec'.format(
            spec=spec))

    def physical_pin(self, function):
        # Just not raising an exception here is needed to prevent a
        # warning in the PiPin constructor
        return None

    def pulled_up(self, function):
        # Assume no external pulls
        return False


class GenericFactory(LGPIOFactory):
    """ PinFactory for zerogpio that can be run on any board, without any knowledge of the board and pinout. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._info = GenericInfo()

        # Revert the hack in LocalPiFactory that causes all factories to share
        # the same reservations dictionary. This hack assumes that different
        # factories are different ways to access the same pins, but in this
        # case different factories access different gpiochips, so make sure
        # that secondary chips use their own reservation list.
        if self._chip != 0:
            self.pins = {}
            self._reservations = defaultdict(list)
            self._res_lock = Lock()

    def spi(self, **spi_args):
        # Could probably be easily supported (by requiring port/device
        # to be passed instead of pins), but gpiozero.pi.spi_port_device
        # currently hardcodes Rpi SPI pin assignment (and is not a
        # method, so we cannot override it here). We can probably just
        # replace PiFactory.spi() completely, though.
        raise PinSPIUnsupported(  # pragma: no cover
            'SPI not supported by this pin factory')


def configure_pin_factory() -> None:
    """
    Configures GPIOZero with a dict of chipnum to of :class:`GenericFactory` if possible, otherwise falls back to :class:`MockFactory`.
    """

    logger = get_logger()

    chipnums = set(desc.chipnum for desc in RaspberryPiPinIds)

    try:
        pin_factories = {chipnum: GenericFactory(chip=chipnum) for chipnum in chipnums}
    # noinspection PyBroadException
    except Exception as e:
        mock = MockFactory()
        pin_factories = {chipnum: mock for chipnum in chipnums}
        logger.warning(f'Failed GPIO chip initialization, all pin interactions will be mocked.', exc_info = e)

    Device.pin_factories = pin_factories
