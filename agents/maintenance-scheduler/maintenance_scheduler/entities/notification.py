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

"""Notification entity module."""

from pydantic import BaseModel, Field, ConfigDict


class MaintenanceNotification(BaseModel):
    """
    Bus stop maintenance notification
    """

    bus_stop_id: str = Field(description="Bus stop id")
    schedule_time: str = Field(description="Scheduled time of the maintenance")
    reason: str = Field(description="Reason why maintenance is scheduled")
    street: str = Field(description="Bus stop address")
    city: str = Field(description="Bus stop city")
    state: str = Field(description="Bus stop state")
    zip: str = Field(description="Bus stop zip")
    image: str = Field(description="Image of the bus stop")
    model_config = ConfigDict(from_attributes=True)


class Email(BaseModel):
    """
    Email components
    """

    email_subject: str = Field(description="Email subject")
    email_body: str = Field(description="Body of the email")
    model_config = ConfigDict(from_attributes=True)
