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

variable "project_id" {
  description = "Project where all the resources will be created"
  type        = string
}
variable "region" {
  description = "Region where the resources will be created"
  default     = "us-central1"
  type        = string
}
variable "bigquery_dataset_location" {
  description = "BigQuery region where the datasets will be created"
  default     = "us-central1"
  type        = string
}
variable "processing_schedule" {
  description = "Schedule of running image processing jobs"
  default     = "*/3 * * * *"
  type        = string
}

variable "pause_scheduler" {
  description = "Pause the scheduler which runs images processing jobs"
  default     = true
  type        = bool
}
variable "notification_email" {
  description = "Email address to send new incident alert notifications"
  type        = string
}

variable "default_multimodal_vertex_ai_model" {
  description = "Name of the default multimodal model"
  type = string
  default = "gemini-2.0-flash-lite-001"
}

variable "pro_multimodal_vertex_ai_model" {
  description = "Name of the advanced multimodal model"
  type = string
  default = "gemini-2.0-flash-001"
}

variable "text_embeddings_vertex_ai_model" {
  description = "Name of the text embedding model"
  type = string
  default = "text-embedding-005"
}

variable "multimodal_embeddings_vertex_ai_model" {
  description = "Name of the multimodal embedding model"
  type = string
  default = "multimodalembedding@001"
}