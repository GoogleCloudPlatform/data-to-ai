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
import random
from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo

from google.api_core.client_info import ClientInfo
from google.cloud import bigquery

from maintenance_scheduler.config import Config
from maintenance_scheduler.entities.bus_stop import BusStop, BusStopIncident, \
    USAddress

bigquery_client = bigquery.Client(client_info=ClientInfo(
    user_agent="cloud-solutions/data-to-ai-agents-scheduler-usage-v1"))

config = Config()

logger = logging.getLogger(__name__)

time_zone = ZoneInfo("america/new_york")


def get_unresolved_incidents() -> List[BusStopIncident]:
    # TODO: fix the example
    """
      Get a list of unresolved bus stop incidents.

      Returns:
          list: List of bust stop incidents

      Example:
          >>> get_unresolved_incidents()
          [BusStopIncident(bus_stop=BusStop(id="123", street='123 Main', city='Anytown', state='CA', zip='94100'), source_image_uri='https://storage.mtls.cloud.google.com/event-processing-demo-multimodal/sources/MA-02-broken-glass.jpg', status='open')]
      """

    logger.info("Getting the list of incidents")
    if config.mock_tools:
        return [
            BusStopIncident(
                status="open",
                bus_stop=BusStop(
                    id='stop-1',
                    address=USAddress(street="123 Main", city="New York",
                                      state="NY", zip="10001")),
                source_image_uri=f"https://storage.mtls.cloud.google.com/{config.CLOUD_PROJECT}-multimodal/sources/MA-02-broken-glass.jpg",
                source_image_mime_type="image/jpeg"),
            BusStopIncident(
                status="open",
                bus_stop=BusStop(
                    id='stop-2',
                    address=USAddress(
                        street="457 1st Street", city="New York", state="NY",
                        zip="10002")),
                source_image_uri="https://storage.mtls.cloud.google.com/{config.CLOUD_PROJECT}-multimodal/sources/MC-02-dirty-damaged.jpg",
                source_image_mime_type="image/jpeg")
        ]
    rows = bigquery_client.query_and_wait(
        project=config.get_bigquery_run_project(),
        query=f"""
        SELECT incidents.incident_id, incidents.bus_stop_id, incidents.status,
            reports.uri as source_image_uri, reports.content_type as source_image_mime_type,
            reports.description, bus_stops.address
        FROM `{config.get_bigquery_data_project()}.bus_stop_image_processing.incidents` incidents
        JOIN `{config.get_bigquery_data_project()}.bus_stop_image_processing.image_reports` reports
            ON incidents.open_report_id = reports.report_id
        JOIN `{config.get_bigquery_data_project()}.bus_stop_image_processing.bus_stops` bus_stops
            ON incidents.bus_stop_id = bus_stops.bus_stop_id
        WHERE incidents.status = 'OPEN' 
    """
    )

    result = []
    for row in rows:
        result.append(BusStopIncident(
            status=row.status.lower(),
            source_image_uri=row.source_image_uri,
            source_image_mime_type=row.source_image_mime_type,
            description=row.description,
            bus_stop=BusStop(
                id=row.bus_stop_id,
                address=USAddress(
                    street=row.address['street'],
                    city=row.address['city'],
                    state=row.address['state'],
                    zip=row.address['zip'])
            )
        ))

    return result


def get_expected_number_of_passengers(bus_stop_ids: list) -> dict:
    """Provides expected number of passengers for a particular bus stop at some point in the future.

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

    if config.mock_tools:
        result = {}
        for bus_stop_id in bus_stop_ids:
            forecast = []
            base_number_of_passengers = random.randint(5, 20)
            for next_increment in range(10, 3 * 24 * 60, 15):
                forecast.append({'time': (
                    datetime.now(tz=time_zone) + timedelta(
                    minutes=next_increment)
                ).isoformat(), 'number_of_passengers': (
                    base_number_of_passengers + random.randint(3, 10))})
            result[bus_stop_id] = forecast
        return result

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter('bus_stop_ids', "STRING", bus_stop_ids)
        ]
    )

    rows = bigquery_client.query_and_wait(
        job_config=job_config,
        project=config.get_bigquery_run_project(),
        query=f"""
        WITH forecast AS (
            SELECT
              bus_stop_id, forecast_timestamp, 
              CAST(forecast_value AS INT64) as expected_number_of_passengers
            FROM
              AI.FORECAST(
                (SELECT bus_stop_id, event_ts, num_riders
                  FROM `{config.get_bigquery_data_project()}.bus_stop_image_processing.bus_ridership`
                  WHERE bus_stop_id IN UNNEST(@bus_stop_ids)),
                data_col => 'num_riders',
                timestamp_col => 'event_ts',
                model => 'TimesFM 2.0',
                id_cols => ['bus_stop_id'],
                horizon => 500,
                confidence_level => .8)
        )
        SELECT bus_stop_id, forecast_timestamp, expected_number_of_passengers 
            FROM forecast WHERE forecast_timestamp > CURRENT_TIMESTAMP()"""
    )

    result = {}
    for row in rows:
        bus_stop_id = row.bus_stop_id
        forecast = result[bus_stop_id] if bus_stop_id in result else []
        forecast.append(
            {'time': row.forecast_timestamp
            .replace(tzinfo=ZoneInfo('UTC')).astimezone(time_zone)
            .strftime("%m/%d/%Y %H:%M"),
             'number_of_passengers': row.expected_number_of_passengers
             })
        result[bus_stop_id] = forecast

    return result


def schedule_maintenance(
    bus_stop_id: str,
    maintenance_start: str,
    reason: str,
    notification_subject: str,
    notification_content: str
) -> str:
    """
      Schedule a bus stop maintenance

      Args:
          bus_stop_id: The id if the bus stop
          maintenance_start: the date and time of the maintenance work
          reason: Explanation why this bus stop and time was selected
          notification_subject: Subject of the email to send to crew supervisor
          notification_content: Text of the email to send to crew supervisor


      Returns:
        outcome of the scheduling. Can be "success", "failure", or "review"

      Example:
          >>> schedule_maintenance('stop-1', "April 2, 2025, at 3:00 PM EST", "Broken glass is a safety concern and needs to be cleaned right away.", "Bus stop stop-1 maintenance required", "Notification content")

      """

    logger.info(
        f"Scheduling maintenance for {bus_stop_id} at {maintenance_start} "
        f"because: {reason}, subject: {notification_subject}, content: {notification_content}")

    if not config.mock_tools:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter('bus_stop_id', "STRING",
                                              bus_stop_id),
                bigquery.ScalarQueryParameter('maintenance_start', "STRING",
                                              maintenance_start),
                bigquery.ScalarQueryParameter('reason', "STRING", reason),
                bigquery.ScalarQueryParameter('notification_subject', "STRING",
                                              notification_subject),
                bigquery.ScalarQueryParameter('notification_content', "STRING",
                                              notification_content),
            ]
        )
        bigquery_client.query_and_wait(
            project=config.get_bigquery_run_project(),
            query=f"""
        UPDATE `{config.get_bigquery_data_project()}.bus_stop_image_processing.incidents`
        SET status = 'SCHEDULED', 
            maintenance_details = STRUCT(
            @maintenance_start as scheduled_time, 
            @reason as reason, 
            @notification_subject as notification_subject, 
            @notification_content as notification_body)
        WHERE status = 'OPEN' and bus_stop_id = @bus_stop_id
    """, job_config=job_config
        )

    return "success"


def get_current_time() -> str:
    """
      Returns current time

      Returns:
          Current time in New York, NY, USA

      Example:
          >>> get_current_time()
          'Mon 28 Apr 2025, 12:41PM'
      """

    logger.info("Getting current time")

    return datetime.now(tz=time_zone).strftime('%a %d %b %Y, %I:%M%p')


def is_time_on_weekend(day: int, month: int, year: int) -> bool:
    """
    Returns:
         a Boolean indicating if the current time is on the weekend
    """

    date = datetime(year, month, day)

    return date.weekday() > 4
