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
    model: str = Field(description="Model used by the agent")


class Config(BaseSettings):
    """Configuration settings for the scheduling agent."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../.env"
        ),
        env_prefix="GOOGLE_",
        case_sensitive=True,
    )
    root_agent_settings: AgentModel = Field(
        default=AgentModel(name="maintenance_scheduler",
                           description="Bus maintenance scheduler",
                           model="gemini-2.5-pro"))
    email_generator_agent_settings: AgentModel = Field(
        default=AgentModel(name="email_notification_generator",
                           description="Email content generator",
                           model="gemini-2.0-flash-001"))
    app_name: str = "Maintenance Scheduler Agent"
    autonomous: bool = Field(default=False,
                             description="Indicates if agent needs to work autonomously (without prompting the user)")
    CLOUD_PROJECT: str = Field()
    CLOUD_BIGQUERY_DATA_PROJECT: str = Field(default="")
    CLOUD_BIGQUERY_RUN_PROJECT: str = Field(default="")
    CLOUD_LOCATION: str = Field(default="us-central1")
    AGENT_RESOURCE_NAME: str = Field(default="UNKNOWN")
    GENAI_USE_VERTEXAI: str = Field(default="1")
    AGENTSPACE_APP_ID: str = Field(default="None", description="Agentspace app id. Only used when deployment to Agentspace is needed.")
    API_KEY: str | None = Field(default="")
    mock_tools: bool = Field(
        default=False,
        description="Indicates if tools need to produce mock output")
    show_thoughts: bool = Field(
        default=True,
        description="Show model's thoughts")
    #Conversational analtyics API configuration 
    CA_API_AGENT_ID: str = Field(default="data_agent_ca_bigquery")
    BQ_DATASET: str = Field(default="bus_stop_image_processing")  

    def get_bigquery_data_project(self) -> str:
        return self.CLOUD_BIGQUERY_DATA_PROJECT or self.CLOUD_PROJECT

    def get_bigquery_run_project(self) -> str:
        return self.CLOUD_BIGQUERY_RUN_PROJECT or self.CLOUD_PROJECT
