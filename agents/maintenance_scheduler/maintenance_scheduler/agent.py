# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.§

"""Agent module for the maintenance scheduling agent."""

import logging
import warnings

from google.adk import Agent
from google.genai import types

from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from .shared_libraries.callbacks import (
  rate_limit_callback,
  before_agent,
  before_tool,
)
from .tools.tools import (
  get_unresolved_incidents,
  get_expected_number_of_passengers,
  schedule_maintenance
)

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

configs = Config()

# configure logging __name__
logger = logging.getLogger(__name__)

safety_settings = [
  types.SafetySetting(
      category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
      threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
  ),
]

generate_content_config = types.GenerateContentConfig(
    safety_settings=safety_settings,
    temperature=0.3,
    max_output_tokens=3000,
    top_k=0.1,
    top_p=0.95,
)

root_agent = Agent(
    name=configs.agent_settings.name,
    model=configs.agent_settings.model,
    global_instruction=GLOBAL_INSTRUCTION,
    instruction=INSTRUCTION,
    tools=[
      get_unresolved_incidents,
      get_expected_number_of_passengers,
      schedule_maintenance
    ],
    before_tool_callback=before_tool,
    before_agent_callback=before_agent,
    before_model_callback=rate_limit_callback,
)
