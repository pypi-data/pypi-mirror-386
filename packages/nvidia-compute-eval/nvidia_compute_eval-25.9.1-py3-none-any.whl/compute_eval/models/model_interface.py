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

import time
from openai import OpenAI
from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError


class ModelInterface:
    """
    Base class for generating code completions.
    """

    def generate_response(self, system_prompt, prompt, params):
        """
        Generate code completions by communicating with the OpenAI API.

        Args:
            system_prompt (str, optional): The system prompt to use for generating completions.
            problem (dict): The dictionary containing the problem prompt.
            model_type (str): The type of the model ("instruct" or "base").
            temperature (float): Temperature for sampling.
            max_tokens (int): Maximum tokens to generate.

        Returns:
            str: Generated code completion.
        """

        messages = []

        if system_prompt is not None:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        max_retries = get_parameter_value("max_retries", params, 0)
        
        if max_retries > 6:
            print(f"Warning: max_retries capped from {max_retries} to 6 to prevent excessive wait times")
            max_retries = 6
        
        retry_count = 0

        while retry_count <= max_retries:
            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=get_parameter_value("temperature", params, 0.2),
                    top_p=get_parameter_value("top_p", params, 0.95),
                    max_tokens=get_parameter_value("max_tokens", params, 2048),
                    stream=False,
                    timeout=get_parameter_value("timeout", params, 3600),
                )
                break  # Success, exit the retry loop
            except Exception as e:
                if retry_count < max_retries:
                    print(f"API call failed: {str(e)}. Retrying in {2 ** retry_count} seconds... (attempt {retry_count + 1}/{max_retries + 1})")
                    time.sleep(2 ** retry_count)
                    retry_count += 1
                else:
                    print(f"API call failed after all retries: {str(e)}. Returning empty response.")
                    return ""
        
        try:
            completion = response.choices[0].message.content
        except Exception as e:
            print(f"There was an error when accessing the completion: {str(e)}")
            completion = ""


        return completion


def get_parameter_value(parameter, parameters, default_value):
    if parameters is not None and parameter in parameters:
        return parameters[parameter]
    else:
        return default_value
