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

# A single service account is used to both schedule processing and actually execute queries
# In many production environments two separate service accounts would be used. In this demo
# we are only using a single account.
resource "google_project_service_identity" "aiplatform_service_accounts" {
  provider = google-beta

  project = var.project_id
  service = "aiplatform.googleapis.com"
}

data "google_project" "agent_deployment_project" {
  project_id = var.project_id
}

locals {
  member_agent_engine_sa = "serviceAccount:service-${data.google_project.agent_deployment_project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "agent_engine_sa_bigquery_job_user" {
  depends_on = [google_project_service_identity.aiplatform_service_accounts]
  member  = local.member_agent_engine_sa
  project = var.project_id
  role    = "roles/bigquery.jobUser"
}

resource "google_bigquery_table_iam_member" "agent_engine_sa_bigquery_editor" {
  depends_on = [google_project_service_identity.aiplatform_service_accounts]
  member = local.member_agent_engine_sa
  role   = "roles/bigquery.dataEditor"
  dataset_id = google_bigquery_dataset.bus-stop-image-processing.dataset_id
  for_each = tomap({
    "incidents" = google_bigquery_table.incidents.id,
  })
  table_id = each.value
}

resource "google_bigquery_table_iam_member" "agent_engine_sa_bigquery_viewer" {
  depends_on = [google_project_service_identity.aiplatform_service_accounts]
  member = local.member_agent_engine_sa
  role   = "roles/bigquery.dataViewer"
  dataset_id = google_bigquery_dataset.bus-stop-image-processing.dataset_id
  for_each = tomap({
    "image_reports" = google_bigquery_table.image_reports.id,
    "bus_stops" = google_bigquery_table.bus_stops.id,
  })
  table_id = each.value
}