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

import asyncio
import time
from typing import Dict, Iterator, List, NamedTuple

from gpiozero import Device, PinUnsupported
from pydantic import ValidationError

from endrpi.model.action_result import ActionResult, error_action_result, success_action_result
from endrpi.model.message import MessageData, PinMessage
from endrpi.model.pin import PinConfiguration, PinDrivenState, PinEdges, RaspberryPiPinIds, PinIo, PinPull, PinConfigurationMap


class PinEvent(NamedTuple):
    ticks: int
    state: int


def read_pin_configurations(pin_ids: List[RaspberryPiPinIds]) -> ActionResult[PinConfigurationMap]:
    """Returns the result of attempting to read the :class:`~endrpi.model.pin.PinConfiguration` of every pin.

    .. note:: A read error on a single pin will cause an error result.
    """

    pin_state_map: Dict[str, PinConfiguration] = {}

    for pin_id in pin_ids:
        pin_state_action_result = read_pin_configuration(pin_id)
        if pin_state_action_result.success:
            pin_state_map[pin_id.name] = pin_state_action_result.data
        else:
            return error_action_result(pin_state_action_result.error.message)

    return success_action_result(pin_state_map)


def read_pin_configuration(pin_id: RaspberryPiPinIds) -> ActionResult[PinConfiguration]:
    """Returns the result of attempting to read the :class:`~endrpi.model.pin.PinConfiguration` of a given pin."""

    try:
        gpiozero_pin = Device.pin_factories[pin_id.chipnum].pin(pin_id.linenum)
    except PinUnsupported:
        return error_action_result(PinMessage.ERROR_UNSUPPORTED__PIN_ID__.format(pin_id=pin_id))

    # Uppercase both gpiozero string values because pin enumerations are uppercase
    gpiozero_pin_function = gpiozero_pin.function.upper()
    gpiozero_pin_pull = gpiozero_pin.pull.upper()

    pin_io = PinIo(gpiozero_pin_function)
    pin_state = gpiozero_pin.state
    pin_pull = PinPull(gpiozero_pin_pull)

    try:
        pin_configuration = PinConfiguration(io=pin_io, state=pin_state, pull=pin_pull)
        return success_action_result(pin_configuration)
    except ValidationError:
        return error_action_result(PinMessage.ERROR_VALIDATION)


def update_pin_configuration(pin_id: RaspberryPiPinIds,
                             pin_configuration: PinConfiguration) -> ActionResult[MessageData]:
    """
    Returns the result of updating the :class:`~endrpi.model.pin.PinConfiguration` of a given pin.

    .. note::
        Ignores 'state' when 'io' is set to INPUT.

    .. note::
        Ignores 'pull' when 'io' is set to OUTPUT.
    """

    try:
        gpiozero_pin = Device.pin_factories[pin_id.chipnum].pin(pin_id.linenum)
    except PinUnsupported:
        return error_action_result(PinMessage.ERROR_UNSUPPORTED__PIN_ID__.format(pin_id=pin_id))

    if pin_configuration.io is PinIo.INPUT:
        if not pin_configuration.pull:
            return error_action_result(PinMessage.ERROR_NO_INPUT_PULL)
        # Don't set pin output state on an input pin
        gpiozero_pin.function = pin_configuration.io.lower()
        gpiozero_pin.pull = pin_configuration.pull.lower()
    else:
        if pin_configuration.state is None:
            return error_action_result(PinMessage.ERROR_NO_OUTPUT_STATE)
        # Don't set pin pull on an output pin
        gpiozero_pin.function = pin_configuration.io.lower()
        gpiozero_pin.state = pin_configuration.state

    message_data = MessageData(message=PinMessage.SUCCESS_UPDATED__PIN_ID__.format(pin_id=pin_id))
    return success_action_result(message_data)


async def check_pin_driven(pin_id: RaspberryPiPinIds) -> ActionResult[PinDrivenState]:
    """Checks whether a pin is externally driven."""

    try:
        gpiozero_pin = Device.pin_factories[pin_id.chipnum].pin(pin_id.linenum)
    except PinUnsupported:
        return error_action_result(PinMessage.ERROR_UNSUPPORTED__PIN_ID__.format(pin_id=pin_id))

    old_pull = gpiozero_pin.pull

    driven = False

    try:
        # Try a couple of times, to rule out the possibility that the pin is driven
        # but the driver switches exactly when we switch the pull resistor.
        for pull, expected_state in [('up', True), ('down', False)] * 3:
            gpiozero_pin.pull = pull
            # Wait a very short while for the pin to change value. Required time
            # depends on the pull resistor and parasitic capacitance, but if we
            # grossly overestimate those, we get an RC time of 1nF * 100kΩ = 100us,
            # and we need two or three RC-times to stabilize, so just stay above
            # that and we should be safe.
            #
            # TODO: This actually blocks the asyncio thread, which is not ideal, but
            # we cannot yield back to asyncio here, then it might serve another
            # task that also tries to control this pin. It would be cleaner to use
            # per-pin locking, but just briefly blocking is easier for now.
            #time.sleep(0.01)
            await asyncio.sleep(0.01)

            # If the pin does not change along with the pull resistor, it must be driven, so stop trying
            print(pull, expected_state, gpiozero_pin.state)
            if gpiozero_pin.state != expected_state:
                driven = True
                break
    finally:
        gpiozero_pin.pull = old_pull

    try:
        pin_driven_status = PinDrivenState(driven=driven)
        return success_action_result(pin_driven_status)
    except ValidationError:
        return error_action_result(PinMessage.ERROR_VALIDATION)


async def watch_pin(pin_id: RaspberryPiPinIds, edges: PinEdges) -> Iterator[PinEvent]:
    """
    Configures a pin for input with the given pull. Monitors its state and returns all changes.
    """

    # try:
    gpiozero_pin = Device.pin_factories[pin_id.chipnum].pin(pin_id.linenum)
    # TODO: How to return an error? Raise?
    # except PinUnsupported:
    #    return error_action_result(PinMessage.ERROR_UNSUPPORTED__PIN_ID__.format(pin_id=pin_id))

    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    # This is called from the lgpio thread on pin events. Use
    # call_soon_threadsafe to something to run in the asyncio loop, and then
    # use create_task to ensure that the async queue.put is actually awaited
    # (if the queue is full it can block).
    def when_changed(ticks, state):
        loop.call_soon_threadsafe(lambda: loop.create_task(queue.put(PinEvent(ticks, state))))

    # TODO: There is probably a race condition here. Low-level gpiod (i.e.
    # kernel) seems to synthesise an event atomically when starting to monitor
    # a pin, but it seems lgpio gpiozero supresses that event maybe?
    yield PinEvent(ticks=0, state=gpiozero_pin.state)

    gpiozero_pin.edges = edges.lower()
    gpiozero_pin.when_changed = when_changed

    # TODO: Handle termination of server
    while True:
        yield await queue.get()
