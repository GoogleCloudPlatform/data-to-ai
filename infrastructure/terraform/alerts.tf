# Copyright 2024 Google LLC
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

resource "google_monitoring_alert_policy" "incident_alert" {
  # disable this resource, but leave for reference
  count = 0
  display_name = "New Bus Stop Incident Alert Policy"
  combiner     = "OR"

  conditions {
    display_name = "Log Match Condition"
    condition_matched_log {
      filter = <<EOF
resource.type="bigquery_dataset" AND
resource.labels.dataset_id="${google_bigquery_dataset.bus-stop-image-processing.dataset_id}" AND
protoPayload.resource_name:"/tables/${google_bigquery_table.incidents.table_id}" AND
protoPayload.metadata.tableDataChange.insertedRowsCount > 0
EOF
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "300s" # Not more than one notification every 5 minutes
    } 
  }

  notification_channels = [google_monitoring_notification_channel.email_channel.id]
  project               = var.project_id
  depends_on = [
    google_bigquery_dataset.bus-stop-image-processing,
    google_bigquery_table.incidents
  ]
}


resource "google_monitoring_notification_channel" "email_channel" {
  display_name = "Email Notifications"
  type         = "email"
  labels = {
    email_address = var.notification_email
  }
  project = var.project_id
}
