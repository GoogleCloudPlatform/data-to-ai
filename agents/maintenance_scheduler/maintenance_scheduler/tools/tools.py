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
"""Tools module for the customer service agent."""

import logging
import random
from datetime import datetime, timedelta, UTC
from typing import List

from maintenance_scheduler.entities.bus_stop import BusStop, BusStopIncident

logger = logging.getLogger(__name__)


def get_unresolved_incidents() -> List[BusStopIncident]:
  """
    Get a list of unresolved bus stop incidents.

    Returns:
        list: List of bust stop incidents

    Example:
        >>> get_unresolved_incidents()
        [BusStopIncident(bus_stop=BusStop(id="123", street='123 Main', city='Anytown', state='CA', zip='94100'), source_image_url='https://storage.mtls.cloud.google.com/event-processing-demo-multimodal/sources/MA-02-broken-glass.jpg', status='open')]
    """

  logger.info("Getting the list of incidents")

  result = [
    BusStopIncident(
        status='open',
        bus_stop=BusStop(
            id='stop-1',
            street="123 Main", city="New York", state="NY", zip="10001"),
        source_image_url='https://storage.mtls.cloud.google.com/event-processing-demo-multimodal/sources/MA-02-broken-glass.jpg'),
    BusStopIncident(
        status='open',
        bus_stop=BusStop(
            id='stop-2',
            street="457 1st Street", city="New York", state="NY", zip="10002"),
        source_image_url='https://storage.mtls.cloud.google.com/event-processing-demo-multimodal/sources/MC-02-dirty-damaged.jpg')
  ]

  return result


def get_expected_number_of_passengers(bus_stop_ids: list) -> dict:
  """Provides expected number of passengers for a particular bus stop at some point in future.

    Args:
        bus_stop_ids: The list of bus stop ids

    Returns:
        A dictionary, where the key is the bus stop id  and the value is the list
        of expected number of passengers at a particular point in time.

    Example:
        >>> get_expected_number_of_passengers(bus_stop_ids=['bus-stop-1', 'bus-stop-2'])
        {"bus-stop-1":
            [{"time": "2025-04-21 18:02:33.463897+00:00", "number_of_passengers":	13},
            {"time": "2025-04-21 18:07:33.463897+00:00", "number_of_passengers":	15},
            {"time": "2025-04-21 18:08:33.463897+00:00", "number_of_passengers":	4}],
        "bus-stop-2":
            [{"time": "2025-04-21 18:02:33.463897+00:00", "number_of_passengers":	5},
            {"time": "2025-04-21 18:07:33.463897+00:00", "number_of_passengers":	7},
            {"time": "2025-04-21 18:08:33.463897+00:00", "number_of_passengers":	10}]
        }
    """
  logger.info("Retrieving expected number of passengers for %s", bus_stop_ids)

  result = {}
  for bus_stop_id in  bus_stop_ids:
    forecast = []
    base_number_of_passengers = random.randint(5, 20);
    for next_increment in range(10, 3 * 24 * 60, 15):
      forecast.append({'time': (
          datetime.now(UTC) + timedelta(minutes=next_increment)
      ).isoformat(), 'number_of_passengers': (base_number_of_passengers + random.randint(3,10))})
    result[bus_stop_id] = forecast
  return result


def schedule_maintenance(bus_stop_id: str, maintenance_start: str, reason: str) -> str:
  """
    Schedule a bus stop maintenance

    Args:
        bus_stop_id: The id if the bus stop
        maintenance_start: the date and time of the maintenance work
        reason: Explanation why this bus stop and time was selected


    Returns:
      outcome of the scheduling. Can be "success", "failure", or "review"

    Example:
        >>> schedule_maintenance('stop-1', "April 25, 2025 at 3:00 PM EST", "Broken glass is a safety concern and needs to be cleaned right away.")

    """

  logger.info(f"Scheduling maintenance for {bus_stop_id} at {maintenance_start} because: {reason}")

  return "success"
