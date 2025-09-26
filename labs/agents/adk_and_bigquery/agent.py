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

from google.adk import Agent
from google.adk.models.google_llm import Gemini
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.genai.types import ThinkingConfig, HttpRetryOptions

from .tools import get_latest_bus_stop_images, mcp_toolset, \
    data_project_id

# configure logging __name__
logger = logging.getLogger(__name__)

# While not important for this agent, can be critical for others
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
]

# This config can fine tune the LLM responses
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
        model="gemini-2.5-flash",
        retry_options=retry_options
    ),
    description="Bus stop image analysis agent",
    instruction=
    f"""You can answer questions about bus stop images. You must use only the provided tools to answer the questions.
    
    If you use the ask-data-insights tool, make sure to provide the table_reference parameter exactly as
    "[{{"projectId": "{data_project_id}", "datasetId":"multimodal", "tableId": "image_reports"}}]. When showing the response of the ask-data-insights tool show the SQL statement provided in the tool return.
    
    If you use the get-table-information tool, make sure to provide the dataset parameter as "multimodal".
    
    If you are asked to describe your capabilities, reply with some variation on the following message. Use the tone of the question to generate the response.
    "I can answer questions about the bus stop images and about BigQuery tables in the multimodal dataset. Try asking these questions:
     - Show the bus stop images
     - Find images containing broken glass
     - What is the breakdown of bus stop cleanliness levels?
     - What tables are in the multimodal dataset?
     - Who has access to the multimodal dataset?
     - What is the schema of the image_reports table?
    "
    """,
    planner=BuiltInPlanner(
        # "Thoughts" will be produced by the LLM and displayed in the UI
        thinking_config=ThinkingConfig(include_thoughts=True)),
    tools=[
        # Custom tool defined in the agent
        get_latest_bus_stop_images,
        # A set of tools provided by a remote MCP server
        mcp_toolset
    ]
)
