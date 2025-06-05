#!/usr/bin/env bash

#
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

set -e
set -u

source .env

display_name="Bus Stop Maintenance Scheduler"
description="Agent to help with bus stop maintenance scheduling"
tool_description="Bus stop maintenance scheduler tool. It looks at the existing open bus stop incidents, prioritizes them and notifies the maintenance crew."
icon_uri="https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/schedule_send/default/24px.svg"

payload=api_data.json

cat > ${payload} << EOF
{
   "displayName": "${display_name}",
   "description": "${description}",
   "icon": {"uri": "${icon_uri}"},
   "adk_agent_definition": {
       "tool_settings": {
           "tool_description": "${tool_description}"
       },
       "provisioned_reasoning_engine": {
           "reasoning_engine": "${GOOGLE_AGENT_RESOURCE_NAME}"
       }
   }
}
EOF

echo "Data to post:"
cat ${payload}

GOOGLE_CLOUD_PROJECT_NUMBER=$(gcloud projects describe ${GOOGLE_CLOUD_PROJECT} --format="value(projectNumber)")

curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "x-goog-user-project: ${GOOGLE_CLOUD_PROJECT}" \
https://discoveryengine.googleapis.com/v1alpha/projects/${GOOGLE_CLOUD_PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${AGENTSPACE_APP_ID}/assistants/default_assistant/agents -d "@${payload}"

rm "${payload}"