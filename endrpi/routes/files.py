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

import os
import re
from fastapi import APIRouter, status

from endrpi.actions.files import read_file, write_file
from endrpi.model.message import FilesMessage, MessageData
from endrpi.utils.api import http_response
from endrpi.model.action_result import error_action_result

directory = os.path.expanduser("~/endrpi-files/")

# Router that is exported to the server
router = APIRouter()

def validate_file_name(file_name: str):
#   Alphanumeric characters and _-. (this also checks for consecutives .)
    pattern = r'^[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*(?:\.[a-zA-Z0-9_-]+)?$'
    return re.match(pattern, file_name)


@router.get(
    '/files/{file_name}',
    name='Get data from given file.',
    description='Gets file data for a specific file.',
    responses={
        status.HTTP_200_OK: {
            'model': bytes
        },
        status.HTTP_404_NOT_FOUND: {
            'model': MessageData,
            'description': FilesMessage.ERROR_NOT_FOUND__FILE__,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            'model': MessageData,
            'description': 'An error occurred',
        }
    }
)
async def get_file_data(file_name: str):
    if validate_file_name(file_name):
        file_path = directory + file_name
        if os.path.exists(file_path):
            file_action_result = await read_file(file_path)
            return http_response(file_action_result)
        else:
            file_action_result = error_action_result(FilesMessage.ERROR_NOT_FOUND__FILE__.format(file_name=file_name))
            return http_response(file_action_result, status.HTTP_404_NOT_FOUND)
    else:
        file_action_result = error_action_result(FilesMessage.ERROR_VALIDATION)
        return http_response(file_action_result, status.HTTP_400_BAD_REQUEST)

@router.put(
    '/files/{file_name}',
    name='Put data in given file.',
    description='Puts data inside a specific file.',
    responses={
        status.HTTP_200_OK: {
            'model': MessageData
        },
        status.HTTP_400_BAD_REQUEST: {
            'model': MessageData,
            'description': FilesMessage.ERROR_VALIDATION,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            'model': MessageData,
            'description': 'An error occurred',
        }
    }
)
async def set_file_data(file_name: str, data: dict):
    if validate_file_name(file_name):
        file_action_result = await write_file(directory, file_name, data)
        return http_response(file_action_result)
    else:
        file_action_result = error_action_result(FilesMessage.ERROR_VALIDATION)
        return http_response(file_action_result, status.HTTP_400_BAD_REQUEST)
