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

data "local_file" "describe_image_prompt_config" {
  filename = "${path.module}/../../prompts/describe-image.prompt.yaml"
}

locals {
  prompt_config = yamldecode(data.local_file.describe_image_prompt_config.content)
}

resource "google_bigquery_routine" "clean_generate_text_json_response_function" {
  dataset_id   = local.dataset_id
  routine_id   = "clean_generate_text_json_response"
  routine_type = "SCALAR_FUNCTION"
  language     = "SQL"

  definition_body = file("${path.module}/bigquery-routines/clean-generate-text-json-response.sql.tftpl")

  arguments {
    name      = "input"
    data_type = "{\"typeKind\" :  \"STRING\"}"
  }
  return_type = "{\"typeKind\" :  \"STRING\"}"

}

resource "google_bigquery_routine" "process_images_procedure" {
  dataset_id   = local.dataset_id
  routine_id   = "process_images"
  routine_type = "PROCEDURE"
  language     = "SQL"
  depends_on   = [
    time_sleep.wait_for_default_model_creation,
    time_sleep.wait_for_text_embedding_model_creation,
    time_sleep.wait_for_multimodal_embedding_model_creation,
    google_bigquery_routine.clean_generate_text_json_response_function
  ]

  definition_body = templatefile("${path.module}/bigquery-routines/process-images.sql.tftpl", {
    process_watermark_table           = "${local.fq_dataset_id}.${google_bigquery_table.process_watermark.table_id}"
    images_table                      = "${local.fq_dataset_id}.${google_bigquery_table.images.table_id}"
    reports_table                     = "${local.fq_dataset_id}.${google_bigquery_table.image_reports.table_id}"
    multimodal_model                  = "${local.fq_dataset_id}.${local.default_model_name}"
    text_embeddings_table             = "${local.fq_dataset_id}.${google_bigquery_table.text_embeddings.table_id}"
    text_embeddings_model              = "${local.fq_dataset_id}.${local.text_embedding_model_name}"
    multimodal_embeddings_table       = "${local.fq_dataset_id}.${google_bigquery_table.multimodal_embeddings.table_id}"
    multimodal_embedding_model        = "${local.fq_dataset_id}.${local.multimodal_embedding_model_name}"
    multimodal_model_id               = var.default_multimodal_vertex_ai_model
    text_embeddings_model_id          = var.text_embeddings_vertex_ai_model
    multimodal_embeddings_model_id    = var.multimodal_embeddings_vertex_ai_model
    prompt                            = local.prompt_config.prompt
    temperature                       = local.prompt_config.temperature
    max_output_tokens                 = local.prompt_config.max_output_tokens
    clean_generate_text_json_function = "${local.fq_dataset_id}.${google_bigquery_routine.clean_generate_text_json_response_function.routine_id}"
  })
}

resource "google_bigquery_routine" "semantic_search_text_embeddings_tvf" {
  dataset_id   = local.dataset_id
  routine_id   = "semantic_search_text_embeddings"
  routine_type = "TABLE_VALUED_FUNCTION"
  language     = "SQL"

  depends_on = [time_sleep.wait_for_text_embedding_model_creation]

  definition_body = templatefile("${path.module}/bigquery-routines/semantic-search-text-embeddings.sql.tftpl", {
    text_embeddings_table = "${local.fq_dataset_id}.${google_bigquery_table.text_embeddings.table_id}"
    text_embedding_model  = "${local.fq_dataset_id}.${local.text_embedding_model_name}"
    reports_table         = "${local.fq_dataset_id}.${google_bigquery_table.image_reports.table_id}"
    max_number_of_results = 10
  })
  arguments {
    name          = "search_terms"
    argument_kind = "FIXED_TYPE"
    data_type     = jsonencode({ "typeKind" : "STRING" })
  }
}

resource "google_bigquery_routine" "semantic_search_multimodal_embeddings_tvf" {
  dataset_id   = local.dataset_id
  routine_id   = "semantic_search_multimodal_embeddings"
  routine_type = "TABLE_VALUED_FUNCTION"
  language     = "SQL"

  depends_on = [time_sleep.wait_for_multimodal_embedding_model_creation]

  definition_body = templatefile("${path.module}/bigquery-routines/semantic-search-multimodal-embeddings.sql.tftpl", {
    multimodal_embeddings_table = "${local.fq_dataset_id}.${google_bigquery_table.multimodal_embeddings.table_id}"
    multimodal_embedding_model  = "${local.fq_dataset_id}.${local.multimodal_embedding_model_name}"
    reports_table               = "${local.fq_dataset_id}.${google_bigquery_table.image_reports.table_id}"
    max_number_of_results       = 10
  })
  arguments {
    name          = "search_terms"
    argument_kind = "FIXED_TYPE"
    data_type     = jsonencode({ "typeKind" : "STRING" })
  }
}

resource "google_bigquery_routine" "update_incidents_procedure" {
  dataset_id      = local.dataset_id
  routine_id      = "update_incidents"
  routine_type    = "PROCEDURE"
  language        = "SQL"
  definition_body = templatefile("${path.module}/bigquery-routines/update-incidents-procedure.sql.tftpl", {
    report_watermark_table = "${local.fq_dataset_id}.${google_bigquery_table.report_watermark.table_id}"
    incidents_table        = "${local.fq_dataset_id}.${google_bigquery_table.incidents.table_id}"
    reports_table          = "${local.fq_dataset_id}.${google_bigquery_table.image_reports.table_id}"
  })
}
