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
# limitations under the License.§

"""Script to run the bus maintenance scheduler deployed at Agent Engine"""

import pprint

import vertexai

from maintenance_scheduler.config import Config

configs = Config()

vertexai.init(
    project=configs.CLOUD_PROJECT,
    location=configs.CLOUD_LOCATION
)

# get the agent based on resource id
remote_app = vertexai.agent_engines.get(configs.AGENT_RESOURCE_NAME)

user_id = "supervisor"
session = remote_app.create_session(user_id=user_id)

for event in remote_app.stream_query(
    user_id=user_id,
    session_id=session["id"],
    message="Check if there are bus stops which need maintenance",
):
    pprint.pp(event)
