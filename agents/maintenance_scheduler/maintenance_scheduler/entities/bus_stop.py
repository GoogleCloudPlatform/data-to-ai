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
"""Customer entity module."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

class BusStop(BaseModel):
    """
    Represents a bus stop.
    """

    id: str
    street: str
    city: str
    state: str
    zip: str
    model_config = ConfigDict(from_attributes=True)


class BusStopIncident(BaseModel):
    """
    Represents an incident with a bus stop.
    """

    bus_stop: BusStop
    source_image_url: str
    # TODO: make an enum
    status: str
    model_config = ConfigDict(from_attributes=True)
