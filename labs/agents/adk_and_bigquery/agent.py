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
from .tools import get_latest_bus_stop_images

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
    name="bigquery_interaction_demo_agent",
    generate_content_config=generate_content_config,
    model=Gemini(
        model="gemini-2.5-pro",
        retry_options=retry_options
    ),
    description="Bus stop image analysis agent",
    global_instruction="",
    instruction="You are a general knowledge agent.",
    planner=BuiltInPlanner(
        thinking_config=ThinkingConfig(include_thoughts=True)),
    tools=[
        get_latest_bus_stop_images
    ],
    # after_tool_callback=after_tool,
    # before_model_callback=rate_limit_callback,
)