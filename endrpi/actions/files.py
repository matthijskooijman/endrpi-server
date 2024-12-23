#  Copyright (c) 2024 Prisma
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

import json
import os

from endrpi.model.action_result import ActionResult, error_action_result, success_action_result
from endrpi.model.message import FilesMessage

async def read_file(file_path: str) -> ActionResult[bytes]:
    try:
        with open(file_path, 'r') as file:
            file_data = json.load(file)
        return success_action_result(file_data)
    except Exception as e:
        return error_action_result(str(e))

async def write_file(directory: str, file_name: str, data: dict) -> ActionResult[bytes]:
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(directory + file_name, 'w') as file:
            json.dump(data, file, indent=4)
            file.flush()
            os.fsync(file.fileno())
        return success_action_result(FilesMessage.SUCCESS_UPDATED__FILE__.format(file_name=file_name))
    except Exception as e:
        return error_action_result(str(e))
