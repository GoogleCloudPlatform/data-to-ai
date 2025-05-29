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

INSTRUCTION = """
Generate an email explaining the work that needs to be done to fix the bus stop. 
Include the bus stop id, bus stop image, reason for maintenance and the time 
when the maintenance needs to occur.

Return the email subject with the following structure: 
Scheduled maintenance for bus stop #[bus_stop_id] at [scheduled_time]

Return the email body with the following structure: 
The bus stop #[bus_stop_id] needs to be repaired based on the analysis of this image:
[image]

We think that the bus stop or the area around it has these problems: [reason].

The bus stop is located at [street], [city], [state] [zip].

If you find that this request is sent in error, please contact the maintenance
team at (111)555-2222.

Sincerely,

Automated Scheduling Assistant
"""
