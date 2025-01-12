# Instead of generating the JavaScript code from the template we can use environment variables
# to provide the function with the 3 parameters required to process images.
resource "local_file" "invoker-function-index-js" {
  filename = "${path.module}/functions/image-process-invoker/index.js"
  content  = templatefile("${path.module}/functions/image-process-invoker/index.js.tftpl",
    {
      project_id        = var.project_id,
      dataset_id        = local.dataset_id,
      bigquery_location = var.bigquery_dataset_location
    })
}

data "archive_file" "invoker_function_archive" {
  depends_on  = [local_file.invoker-function-index-js]
  type        = "zip"
  output_path = "${path.module}/functions/image-process-invoker/image-process-invoker.zip"
  excludes    = ["*.tftpl", "*.zip", "package-lock.json", "node_modules", ".DS_Store"]
  source_dir  = "${path.module}/functions/image-process-invoker"
}

locals {
  staged_image_process_invoker_code = "functions/image-process-invoker.zip"
}

resource "google_storage_bucket_object" "staged_image_process_invoker" {
  bucket = google_storage_bucket.image_bucket.name
  name   = local.staged_image_process_invoker_code
  source = data.archive_file.invoker_function_archive.output_path
}

# TODO: find out why the function doesn't get re-created if the source code changes.
# At the moment the function needs to be manually deleted in order to be updated.
resource "google_cloudfunctions2_function" "processing_invoker" {
  depends_on = [
    google_project_iam_member.cloud_function_build_sa_roles,
    google_storage_bucket_object.staged_image_process_invoker,
    google_bigquery_routine.process_images_procedure,
    google_bigquery_routine.update_incidents_procedure
  ]
  name     = "image-processing-invoker"
  project  = var.project_id
  location = var.region

  build_config {
    runtime         = "nodejs20"
    entry_point     = "invoke-image-processing"
    service_account = google_service_account.cloud_function_build_sa.id
    source {
      storage_source {
        bucket = google_storage_bucket.image_bucket.name
        object = local.staged_image_process_invoker_code
      }
    }
  }

  service_config {
    service_account_email = google_service_account.data_processor_sa.email
    ingress_settings      = "ALLOW_INTERNAL_ONLY"
  }
}

resource "google_cloud_run_service_iam_member" "processing_invoker_permissions" {
  project  = google_cloudfunctions2_function.processing_invoker.project
  location = google_cloudfunctions2_function.processing_invoker.location
  service  = google_cloudfunctions2_function.processing_invoker.name
  role     = "roles/run.invoker"
  member   = local.member_data_processor_sa
}