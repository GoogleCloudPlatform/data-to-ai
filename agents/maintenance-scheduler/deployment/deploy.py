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

import argparse
import logging
import sys

import vertexai
from google.api_core.exceptions import NotFound
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

from maintenance_scheduler.agent import root_agent
from maintenance_scheduler.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

configs = Config()

STAGING_BUCKET = f"gs://{configs.CLOUD_PROJECT}-" \
                 f"maintenance-scheduler-agent-staging"

AGENT_WHL_FILE = "./maintenance_scheduler-0.1.0-py3-none-any.whl"

vertexai.init(
    project=configs.CLOUD_PROJECT,
    location=configs.CLOUD_LOCATION,
    staging_bucket=STAGING_BUCKET,
)

parser = argparse.ArgumentParser(
    description="Bus stop maintenance scheduler app")

parser.add_argument(
    "--delete",
    action="store_true",
    dest="delete",
    required=False,
    help="Delete deployed agent",
)
parser.add_argument(
    "--resource_id",
    required="--delete" in sys.argv,
    action="store",
    dest="resource_id",
    help="The resource id of the agent to be deleted in the format "
         "projects/PROJECT_ID/locations/LOCATION/reasoningEngines/ENGINE_ID",
)

args = parser.parse_args()

if args.delete:
    try:
        agent_engines.get(resource_name=args.resource_id)
        agent_engines.delete(resource_name=args.resource_id, force=True)
        logging.info(f"Agent {args.resource_id} deleted successfully")
    except NotFound as e:
        logging.error(e)
        logging.error(f"Agent {args.resource_id} not found")

else:
    app = AdkApp(agent=root_agent, enable_tracing=True)

    logging.info("deploying agent to agent engine:")
    remote_app = agent_engines.create(
        app,
        display_name="Bus Maintenance Scheduler v1.0",
        description="Agent to assist with bus maintenance scheduling",
        requirements=[
            AGENT_WHL_FILE,
        ],
        extra_packages=[AGENT_WHL_FILE],
    )

    user_id = "user"
    logging.debug("testing deployment:")
    session = remote_app.create_session(user_id=user_id)
    need_to_print_resource_name = True
    for event in remote_app.stream_query(
        user_id=user_id,
        session_id=session["id"],
        # We shouldn't ask the agent to schedule any actual maintenance
        # because it will most likely process everything right away.
        message="Is now a weekend?",
    ):
        if need_to_print_resource_name and event.get("content", None):
            logging.info(
                f"Agent deployed successfully under resource name: "
                f"{remote_app.resource_name}"
            )
            need_to_print_resource_name = False
