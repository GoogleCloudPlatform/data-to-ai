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
# limitations under the License.
# add docstring to this module

"""Email content module"""

import logging

from google.adk.agents import Agent
from google.adk.tools import agent_tool

from maintenance_scheduler.config import Config
from maintenance_scheduler.entities.notification import Email

configs = Config()

logger = logging.getLogger(__name__)

email_notification_generator = Agent(
    name=configs.email_generator_agent_settings.name,
    description=configs.email_generator_agent_settings.description,
    model=configs.email_generator_agent_settings.model,
    instruction=
    "Generate an email explaining the work that needs to be done to fix the bus stop. "
    "Include the bus stop id, bus stop image, reason for maintenance and the time when the maintenance needs to occur.",
    # input_schema=MaintenanceNotification,
    output_schema=Email,
    output_key="email"
)

email_content_generator_tool = \
    agent_tool.AgentTool(agent=email_notification_generator)
