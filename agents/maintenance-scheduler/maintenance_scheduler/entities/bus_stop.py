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

"""Bus stop entity module."""

from pydantic import BaseModel, Field


class USAddress(BaseModel):
    """
      Represents an address in USA
    """

    street: str = Field(description="Street or road, including the number")
    city: str = Field(description="City")
    state: str = Field(description="State abbreviation")
    zip: str = Field(description="ZIP code")


class BusStop(BaseModel):
    """
      Represents a bus stop.
    """

    id: str = Field(description="Id of the bus stop")
    address: USAddress = Field(description="Closest address")


class BusStopIncident(BaseModel):
    """
      Represents an incident with a bus stop.
    """

    bus_stop: BusStop = Field(description="Bus stop")
    incident_image_url: str = Field(description="Image URL")
    incident_image_mime_type: str = Field(description="Image mime")
    status: str = Field(description="Status of the incident")
    description: str = Field(description="Description of the bus stop")
