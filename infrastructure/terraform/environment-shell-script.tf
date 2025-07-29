resource "local_file" "cloud_env" {
  filename        = "${path.module}/../../.cloud-env.sh"
  file_permission = "0555"
  content         = <<EOF
export IMAGE_BUCKET=${google_storage_bucket.image_bucket.name}
export PROJECT_ID=${var.project_id}
# We don't have a dedicated BigQuery billing project id in this demo, but for most production
# environments it will be separate from the data project id
export BIGQUERY_RUN_PROJECT_ID=${var.project_id}
export BIGQUERY_DATA_PROJECT_ID=${google_bigquery_dataset.bus-stop-image-processing.project}
export BIGQUERY_DATA_LOCATION=${google_bigquery_dataset.bus-stop-image-processing.location}
EOF
}