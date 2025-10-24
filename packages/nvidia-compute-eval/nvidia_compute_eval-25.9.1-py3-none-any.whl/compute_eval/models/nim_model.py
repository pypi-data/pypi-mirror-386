# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import dotenv
from typing import Optional

from compute_eval.models.model_interface import ModelInterface


class NimModel(ModelInterface):
    """
    Generate code completions using NVIDIA models from NIM.

    Args:
        model_name (str): Name of the NVIDIA model to use for generating completions.
        base_url (str, optional): Base URL for the API endpoint. Defaults to "https://integrate.api.nvidia.com/v1".
    """

    def __init__(self, model_name, base_url: Optional[str] = None):
        dotenv.load_dotenv()
        self.model_name = model_name
        self.base_url = base_url if base_url is not None else "https://integrate.api.nvidia.com/v1"
        self.api_key = os.getenv("NEMO_API_KEY")
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY")
            if self.api_key is None:
                raise Exception("Neither NEMO_API_KEY nor OPENAI_API_KEY found in the .env file.")

    def generate_response(self, system_prompt, prompt, params):
        """
        Interact with the NVIDIA API to generate code completions.
        """

        return super().generate_response(system_prompt, prompt, params)
