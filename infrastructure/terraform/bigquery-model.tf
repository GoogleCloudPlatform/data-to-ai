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

resource "google_bigquery_connection" "vertex_ai_connection" {
  connection_id = "vertex_ai_connection"
  project       = var.project_id
  location      = var.bigquery_dataset_location

  cloud_resource {}
}

locals {
  vertex_ai_connection_sa = format("serviceAccount:%s", google_bigquery_connection.vertex_ai_connection.cloud_resource[0].service_account_id)
}

resource "time_sleep" "wait_for_propagation_of_vertex_ai_connection_sa" {
  depends_on      = [google_bigquery_connection.vertex_ai_connection]
  create_duration = "60s"

  triggers = {
    connection_sa = google_bigquery_connection.vertex_ai_connection.cloud_resource[0].service_account_id
  }
}

resource "google_project_iam_member" "vertex_ai_connection_sa_vertex_ai_user" {
  project    = var.project_id
  role       = "roles/aiplatform.user"
  member     = local.vertex_ai_connection_sa
  depends_on = [time_sleep.wait_for_propagation_of_vertex_ai_connection_sa]
}

resource "time_sleep" "wait_for_propagation_of_vertex_ai_connection_permission" {
  depends_on      = [google_project_iam_member.vertex_ai_connection_sa_vertex_ai_user]
  create_duration = "60s"

  triggers = {
    connection_sa = google_project_iam_member.vertex_ai_connection_sa_vertex_ai_user.member
  }
}

locals {
  default_model_name              = "default_model"
  pro_model_name                  = "pro_model"
  text_embedding_model_name       = "text_embedding_model"
  multimodal_embedding_model_name = "multimodal_embedding_model"
}

resource "random_id" "default_model_job_id_suffix" {
  byte_length = 4
  keepers     = {
    model = var.default_multimodal_vertex_ai_model
  }
}

resource "google_bigquery_job" "create_default_model" {
  job_id     = "create_default_model_${random_id.default_model_job_id_suffix.hex}"
  location   = var.bigquery_dataset_location
  depends_on = [
    time_sleep.wait_for_propagation_of_vertex_ai_connection_permission
  ]
  query {
    query = <<END_OF_STATEMENT
CREATE OR REPLACE MODEL `${var.project_id}.${local.dataset_id}.${local.default_model_name}`
  REMOTE WITH CONNECTION `${google_bigquery_connection.vertex_ai_connection.id}`
  OPTIONS(ENDPOINT = '${var.default_multimodal_vertex_ai_model}');
END_OF_STATEMENT

    create_disposition = ""
    write_disposition  = ""
  }
}

resource "random_id" "pro_model_job_id_suffix" {
  byte_length = 4
  keepers     = {
    model_name = var.pro_multimodal_vertex_ai_model
  }
}
resource "google_bigquery_job" "create_pro_model" {
  job_id     = "create_pro_model_${random_id.pro_model_job_id_suffix.hex}"
  location   = var.bigquery_dataset_location
  depends_on = [
    time_sleep.wait_for_propagation_of_vertex_ai_connection_permission
  ]
  query {
    query = <<END_OF_STATEMENT
CREATE OR REPLACE MODEL `${var.project_id}.${local.dataset_id}.${local.pro_model_name}`
  REMOTE WITH CONNECTION `${google_bigquery_connection.vertex_ai_connection.id}`
  OPTIONS(ENDPOINT = '${var.pro_multimodal_vertex_ai_model}');
END_OF_STATEMENT

    create_disposition = ""
    write_disposition  = ""
  }
}

resource "random_id" "text_embeddings_model_job_id_suffix" {
  byte_length = 4
  keepers     = {
    model_name = var.text_embeddings_vertex_ai_model
  }
}

resource "google_bigquery_job" "create_text_embedding_model" {
  job_id     = "create_text_embedding_model_${random_id.text_embeddings_model_job_id_suffix.hex}"
  location   = var.bigquery_dataset_location
  depends_on = [
    time_sleep.wait_for_propagation_of_vertex_ai_connection_permission
  ]
  query {
    query = <<END_OF_STATEMENT
CREATE OR REPLACE MODEL `${var.project_id}.${local.dataset_id}.${local.text_embedding_model_name}`
  REMOTE WITH CONNECTION `${google_bigquery_connection.vertex_ai_connection.id}`
  OPTIONS(ENDPOINT = '${var.text_embeddings_vertex_ai_model}');
END_OF_STATEMENT

    create_disposition = ""
    write_disposition  = ""
  }
}

resource "random_id" "multimodal_embeddings_model_job_id_suffix" {
  byte_length = 4
  keepers     = {
    model_name = var.multimodal_embeddings_vertex_ai_model
  }
}

resource "google_bigquery_job" "create_multimodal_embedding_model" {
  job_id     = "create_multimodal_embedding_model_${random_id.multimodal_embeddings_model_job_id_suffix.hex}"
  location   = var.bigquery_dataset_location
  depends_on = [
    time_sleep.wait_for_propagation_of_vertex_ai_connection_permission
  ]
  query {
    query = <<END_OF_STATEMENT
CREATE OR REPLACE MODEL `${var.project_id}.${local.dataset_id}.${local.multimodal_embedding_model_name}`
  REMOTE WITH CONNECTION `${google_bigquery_connection.vertex_ai_connection.id}`
  OPTIONS(ENDPOINT = '${var.multimodal_embeddings_vertex_ai_model}');
END_OF_STATEMENT

    create_disposition = ""
    write_disposition  = ""
  }
}

resource "time_sleep" "wait_for_default_model_creation" {
  create_duration = "45s"

  triggers = {
    job_id = google_bigquery_job.create_default_model.job_id
  }
}

resource "time_sleep" "wait_for_text_embedding_model_creation" {
  create_duration = "45s"

  triggers = {
    job_id = google_bigquery_job.create_text_embedding_model.job_id
  }
}

resource "time_sleep" "wait_for_multimodal_embedding_model_creation" {
  depends_on      = [google_bigquery_job.create_multimodal_embedding_model]
  create_duration = "45s"

  triggers = {
    job_id = google_bigquery_job.create_multimodal_embedding_model.job_id
  }
}