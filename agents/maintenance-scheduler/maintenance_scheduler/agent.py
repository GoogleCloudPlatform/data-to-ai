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
from google.adk.models.google_llm import Gemini
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.genai.types import ThinkingConfig, HttpRetryOptions

from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION, AUTONOMOUS_INSTRUCTIONS, \
    INTERACTIVE_INSTRUCTIONS
from .shared_libraries.callbacks import (
    rate_limit_callback,
    after_tool,
)
from .tools.email_content_generator import email_content_generator_tool
from .tools.tools import (
    get_unresolved_incidents_tool,
    get_expected_number_of_passengers_tool,
    schedule_maintenance_tool,
    get_current_time,
    is_time_on_weekend
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
    temperature=0.1,
    max_output_tokens=3000,
    top_k=2,
    top_p=0.95,
)

# For production deployments these options should be provided via configuration
retry_options = HttpRetryOptions(
    attempts=10,
    initial_delay=10,
    max_delay=5000,
    exp_base=1.5,
    jitter=0.5
)
root_agent = Agent(
    name=configs.root_agent_settings.name,
    generate_content_config=generate_content_config,
    model=Gemini(
        model=configs.root_agent_settings.model,
        retry_options=retry_options
    ),
    description=configs.root_agent_settings.description,
    global_instruction=GLOBAL_INSTRUCTION
                       + (AUTONOMOUS_INSTRUCTIONS if configs.autonomous
                          else INTERACTIVE_INSTRUCTIONS),
    instruction=INSTRUCTION,
    planner=BuiltInPlanner(
        thinking_config=ThinkingConfig(include_thoughts=configs.show_thoughts)),
    tools=[
        get_unresolved_incidents_tool,
        get_expected_number_of_passengers_tool,
        schedule_maintenance_tool,
        get_current_time,
        email_content_generator_tool,
        is_time_on_weekend
    ],
    after_tool_callback=after_tool,
    before_model_callback=rate_limit_callback,
)
