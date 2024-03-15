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
import subprocess

from endrpi.config.logging import get_logger
from endrpi.model.action_result import ActionResult, error_action_result, success_action_result
from endrpi.model.message import MessageData

def exec_cmd(cmd: List[str]) -> ActionResult[bytes]:
    try:
        output = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout
        return success_action_result(output)
    except subprocess.CalledProcessError as e:
        return error_action_result(f"Command failed with code {e.returncode}. Command output:\n{e.output.decode()}")
    except OSError as e:
        return error_action_result(f"Command failed to execute: {e}")


