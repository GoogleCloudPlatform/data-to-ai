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

"""Tools module for the maintenance scheduling agent."""

import logging
import os
from typing import List

from google.cloud import bigquery
from google.cloud.bigquery.enums import JobCreationMode
from google.cloud.bigquery.job import QueryJobConfig
from pydantic import BaseModel, Field
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

bigquery_client = bigquery.Client(
    # This can be useful to reduce response latencies
    default_job_creation_mode=JobCreationMode.JOB_CREATION_OPTIONAL
)

logger = logging.getLogger(__name__)

data_project_id=os.getenv("BIGQUERY_DATA_PROJECT_ID")

class BusStop(BaseModel):
    """
      Represents an analyzed image of a bus stop.
    """
    bus_stop_id: str = Field(description="Bus stop id")
    image_url: str = Field(description="Image URL")
    image_mime_type: str = Field(description="Image mime")
    cleanliness_level: int = Field(description="Cleanliness level")
    safety_level: int = Field(description="Safety level")
    description: str = Field(description="Description of the bus stop")

async def get_latest_bus_stop_images(number_of_images: int) -> List[BusStop]:
    logger.info("Getting the list of bus stops")
    bus_stops = []

    try:
        rows = bigquery_client.query_and_wait(
            project=os.getenv("BIGQUERY_RUN_PROJECT_ID"),
            job_config=QueryJobConfig(
                job_timeout_ms=60 * 1000
            ),
            query=f"""
            SELECT bus_stop_id, cleanliness_level, safety_level,
                uri as image_url, 'image/jpeg' as image_mime_type,
                description
            FROM `{data_project_id}.multimodal.image_reports`
            WHERE description != '' 
            ORDER BY updated DESC
            LIMIT {number_of_images}
            """
        )

        for row in rows:
            bus_stops.append(BusStop(
                bus_stop_id=row.bus_stop_id,
                image_url=row.image_url.replace("gs://",
                                    "https://storage.mtls.cloud.google.com/"),
                image_mime_type=row.image_mime_type,
                cleanliness_level=row.cleanliness_level,
                safety_level=row.safety_level,
                description=row.description
            ))
    except Exception as ex:
        logger.error("Call to retrieve bus stops failed: %s", str(ex))
        return {
            "status": "error"
        }

    logger.info("Retrieved bus stops: %s", bus_stops)
    return {
        "status": "success",
        "bus_stops": bus_stops
    }

mcp_toolset=McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://127.0.0.1:5000/mcp/bus-stop-images-toolset",
        headers={"Authorization": "Bearer your-auth-token-in-production"}
    ),
)