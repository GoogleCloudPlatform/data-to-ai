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

resource "google_bigquery_dataset" "bus-stop-image-processing" {
  dataset_id    = "bus_stop_image_processing"
  friendly_name = "Bus Stop Image Processing"
  location      = var.bigquery_dataset_location

  delete_contents_on_destroy = true
}

resource "google_bigquery_connection" "image_bucket_connection" {
  connection_id = "image_bucket_connection"
  project       = var.project_id
  location      = var.bigquery_dataset_location

  cloud_resource {}
}

locals {
  image_bucket_connection_sa = format("serviceAccount:%s", google_bigquery_connection.image_bucket_connection.cloud_resource[0].service_account_id)
  dataset_id                 = google_bigquery_dataset.bus-stop-image-processing.dataset_id
  fq_dataset_id              = "${var.project_id}.${google_bigquery_dataset.bus-stop-image-processing.dataset_id}"
}

resource "time_sleep" "wait_for_propagation_of_bucket_connection_sa" {
  depends_on      = [google_bigquery_connection.image_bucket_connection]
  create_duration = "45s"

  triggers = {
    connection_sa = google_bigquery_connection.image_bucket_connection.cloud_resource[0].service_account_id
  }
}

resource "google_storage_bucket_iam_member" "image_bucket_connection_sa_bucket_viewer" {
  bucket     = google_storage_bucket.image_bucket.name
  role       = "roles/storage.objectViewer"
  member     = local.image_bucket_connection_sa
  depends_on = [time_sleep.wait_for_propagation_of_bucket_connection_sa]
}

resource "google_project_iam_member" "image_bucket_connection_sa_vertex_ai_user" {
  project    = var.project_id
  role       = "roles/aiplatform.user"
  member     = local.image_bucket_connection_sa
  depends_on = [time_sleep.wait_for_propagation_of_bucket_connection_sa]
}

resource "google_bigquery_table" "images" {
  description         = "Object table to access bus stop images"
  deletion_protection = false
  dataset_id          = local.dataset_id
  table_id            = "images"
  max_staleness       = "0-0 0 0:30:0"
  external_data_configuration {
    connection_id       = google_bigquery_connection.image_bucket_connection.id
    source_uris         = [format("gs://%s/images/*", google_storage_bucket.image_bucket.id)]
    object_metadata     = "SIMPLE"
    metadata_cache_mode = "MANUAL"
    autodetect          = false
  }
}

resource "google_bigquery_table" "reports" {
  deletion_protection = false
  dataset_id          = local.dataset_id
  table_id            = "reports"
  description         = "Results of attribute extraction for an individual image"
  clustering          = ["bus_stop_id"]
  schema              = file("${path.module}/bigquery-schema/reports.json")

  table_constraints {
    primary_key {
      columns = ["report_id"]
    }
  }
}

resource "random_id" "reports_search_job_id_suffix" {
  byte_length = 4
  keepers     = {
    table_creation_itme = google_bigquery_table.reports.creation_time
  }
}

resource "google_bigquery_job" "reports_search_index" {
  job_id     = "reports_search_index_${random_id.reports_search_job_id_suffix.hex}"
  depends_on = [google_bigquery_table.reports]

  query {
    query              = "CREATE SEARCH INDEX IF NOT EXISTS reports_search_index ON `${local.fq_dataset_id}.${google_bigquery_table.reports.table_id}` (description)"
    create_disposition = ""
    write_disposition  = ""
  }
  location = var.bigquery_dataset_location
}

resource "google_bigquery_table" "process_watermark" {
  deletion_protection = false
  dataset_id          = local.dataset_id
  table_id            = "process_watermark"
  description         = "Table with a single row which contains the timestamp the data was last processed."
  schema              = file("${path.module}/bigquery-schema/process_watermark.json")
}

resource "random_id" "populate_process_watermark_job_id_suffix" {
  byte_length = 4
  keepers     = {
    table_creation_itme = google_bigquery_table.process_watermark.creation_time
  }
}

resource "google_bigquery_job" "populate_process_watermark" {
  job_id     = "set_initial_process_watermark_${random_id.populate_process_watermark_job_id_suffix.hex}"
  depends_on = [google_bigquery_table.process_watermark]

  query {
    query              = "INSERT INTO ${local.dataset_id}.${google_bigquery_table.process_watermark.table_id} VALUES (TIMESTAMP('2000-01-01 00:00:00+00'))"
    create_disposition = ""
    write_disposition  = ""
  }
  location = var.bigquery_dataset_location
}

resource "google_bigquery_table" "report_watermark" {
  deletion_protection = false
  dataset_id          = local.dataset_id
  table_id            = "report_watermark"
  description         = "Table with a single row which contains the timestamp the report data was last processed."
  schema              = file("${path.module}/bigquery-schema/report_watermark.json")
}

resource "random_id" "populate_report_watermark_job_id_suffix" {
  byte_length = 4
  keepers     = {
    table_creation_itme = google_bigquery_table.report_watermark.creation_time
  }
}

resource "google_bigquery_job" "populate_report_watermark" {
  job_id     = "set_initial_report_watermark_${random_id.populate_report_watermark_job_id_suffix.hex}"
  depends_on = [google_bigquery_table.report_watermark]

  query {
    query              = "INSERT INTO ${local.dataset_id}.${google_bigquery_table.report_watermark.table_id} VALUES (TIMESTAMP('2000-01-01 00:00:00+00'))"
    create_disposition = ""
    write_disposition  = ""
  }
  location = var.bigquery_dataset_location
}

resource "google_bigquery_table" "incidents" {
  deletion_protection = false
  dataset_id          = local.dataset_id
  table_id            = "incidents"
  description         = "Incidents generated based on the attributes of the processed images"
  clustering          = ["bus_stop_id"]
  schema              = file("${path.module}/bigquery-schema/incidents.json")

  table_constraints {
    foreign_keys {
      name = "fk_incidents_open_reports"
      referenced_table {
        project_id = var.project_id
        dataset_id = google_bigquery_dataset.bus-stop-image-processing.dataset_id
        table_id   = google_bigquery_table.reports.table_id
      }
      column_references {
        referencing_column = "open_report_id"
        referenced_column  = "report_id"
      }
    }

    foreign_keys {
      name = "fk_incidents_resolve_reports"
      referenced_table {
        project_id = var.project_id
        dataset_id = google_bigquery_dataset.bus-stop-image-processing.dataset_id
        table_id   = google_bigquery_table.reports.table_id
      }
      column_references {
        referencing_column = "resolve_report_id"
        referenced_column  = "report_id"
      }
    }
  }
}

resource "google_bigquery_table" "text_embeddings" {
  deletion_protection = false
  dataset_id          = local.dataset_id
  table_id            = "text_embeddings"
  description         = "Embeddings generated on the image description produced by the model "
  clustering          = ["report_id"]
  schema              = file("${path.module}/bigquery-schema/text_embeddings.json")

  table_constraints {
    foreign_keys {
      name = "fk_text_embeddings_reports"
      referenced_table {
        project_id = var.project_id
        dataset_id = google_bigquery_dataset.bus-stop-image-processing.dataset_id
        table_id   = google_bigquery_table.reports.table_id
      }
      column_references {
        referencing_column = "report_id"
        referenced_column  = "report_id"
      }
    }
  }
}

resource "google_bigquery_table" "multimodal_embeddings" {
  deletion_protection = false
  dataset_id          = local.dataset_id
  table_id            = "multimodal_embeddings"
  description         = "Multimodal mbeddings of images"
  clustering          = ["report_id"]
  schema              = file("${path.module}/bigquery-schema/multimodal_embeddings.json")

  table_constraints {
    foreign_keys {
      name = "fk_multimodal_embeddings_reports"
      referenced_table {
        project_id = var.project_id
        dataset_id = google_bigquery_dataset.bus-stop-image-processing.dataset_id
        table_id   = google_bigquery_table.reports.table_id
      }
      column_references {
        referencing_column = "report_id"
        referenced_column  = "report_id"
      }
    }
  }
}
