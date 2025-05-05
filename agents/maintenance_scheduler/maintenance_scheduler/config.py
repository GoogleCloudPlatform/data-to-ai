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

"""Configuration module for the maintenance scheduling agent."""

import logging
import os

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AgentModel(BaseModel):
    """Agent model settings."""

    name: str = Field(description="Agent name. Must be a valid identifier")
    description: str = Field(description="Agent description")
    # model: str = Field(default="gemini-2.5-flash-preview-04-17")
    model: str = Field(default="gemini-2.0-flash-001",
                       description="Model used by the agent")


class Config(BaseSettings):
    """Configuration settings for the customer service agent."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../.env"
        ),
        env_prefix="GOOGLE_",
        case_sensitive=True,
    )
    root_agent_settings: AgentModel = Field(
        default=AgentModel(name="maintenance_scheduler", description="Bus maintenance scheduler"))
    email_generator_agent_settings: AgentModel = Field(
        default=AgentModel(name="email_generator", description="Email content generator"))
    app_name: str = "Maintenance Scheduler Agent"
    autonomous: bool = Field(default=True,
                             description="Indicates if agent needs to work autonomously (without prompting the user)")
    CLOUD_PROJECT: str = Field()
    CLOUD_LOCATION: str = Field(default="us-central1")
    AGENT_RESOURCE_ID: str = Field(default="UNKNOWN")
    GENAI_USE_VERTEXAI: str = Field(default="1")
    API_KEY: str | None = Field(default="")
    mock_tools: bool = Field(default=False, description="Indicates if tools need to produce mock output")
