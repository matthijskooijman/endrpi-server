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

from typing import List

from fastapi import APIRouter, status

from endrpi.actions.cmd import exec_cmd
from endrpi.model.action_result import error_action_result
from endrpi.model.message import MessageData
from endrpi.model.cmd import CmdState
from endrpi.utils.api import http_response

cmd_whitelist = [
    "nmcli",
    "pactl",
    "pacmd",
]

# Router that is exported to the server
router = APIRouter()

@router.post(
    '/exec_cmd',
    description='Execute command and return results',
    responses={
        status.HTTP_200_OK: {
            'model': bytes,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            'model': MessageData,
            'description': 'Command failed to execute',
        },
        status.HTTP_403_FORBIDDEN: {
            'model': MessageData,
            'description': 'Command not allowed',
        },
    }
)
async def put_exec_cmd(arg: CmdState):
    if not arg.cmd:
        action_result = error_action_result("Command cannot be empty")
        return http_response(action_result, status.HTTP_500_INTERNAL_SERVER_ERROR)

    if arg.cmd[0] not in cmd_whitelist:
        action_result = error_action_result("Command not allowed. Allowed commands: {}".format(", ".join(cmd_whitelist)))
        return http_response(action_result, status.HTTP_403_FORBIDDEN)

    action_result = await exec_cmd(arg.cmd)
    return http_response(action_result)
