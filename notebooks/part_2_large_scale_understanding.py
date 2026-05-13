# ---
# jupyter:
#   jupytext:
#     comment_magics: false
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.2
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# %% id="y5uylk8B8TegnfJxTcMPklE2"
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not ue this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# %% [markdown] id="yumqITSFiffv"
# # CleanSight (Part 2): Large-scale multimodal understanding
#
# <table align="left">
# <td style="text-align: center">
#   <a href="https://colab.research.google.com/github/GoogleCloudPlatform/data-to-ai/blob/main/notebooks/part_2_large_scale_understanding.ipynb">
#     <img width="32px" src="https://www.gstatic.com/pantheon/images/bigquery/welcome_page/colab-logo.svg" alt="Google Colaboratory logo"><br> Open in Colab
#   </a>
# </td>
# <td style="text-align: center">
#   <a href="https://console.cloud.google.com/vertex-ai/colab/import/https:%2F%2Fraw.githubusercontent.com%2FGoogleCloudPlatform%2Fdata-to-ai%2Fmain%2Fnotebooks%2Fpart_2_large_scale_understanding.ipynb">
#     <img width="32px" src="https://lh3.googleusercontent.com/JmcxdQi-qOpctIvWKgPtrzZdJJK-J3sWE1RsfjZNwshCFgE_9fULcNpuXYTilIR2hjwN" alt="Google Cloud Colab Enterprise logo"><br> Open in Colab Enterprise
#   </a>
# </td>
# <td style="text-align: center">
#   <a href="https://console.cloud.google.com/vertex-ai/workbench/deploy-notebook?download_url=https://raw.githubusercontent.com/GoogleCloudPlatform/data-to-ai/main/notebooks/part_2_large_scale_understanding.ipynb">
#     <img src="https://www.gstatic.com/images/branding/gcpiconscolors/vertexai/v1/32px.svg" alt="Vertex AI logo"><br> Open in Vertex AI Workbench
#   </a>
# </td>
# <td style="text-align: center">
#   <a href="https://console.cloud.google.com/bigquery/import?url=https://github.com/GoogleCloudPlatform/data-to-ai/blob/main/notebooks/part_2_large_scale_understanding.ipynb">
#     <img src="https://www.gstatic.com/images/branding/gcpiconscolors/bigquery/v1/32px.svg" alt="BigQuery Studio logo"><br> Open in BigQuery Studio
#   </a>
# </td>
# <td style="text-align: center">
#   <a href="https://github.com/GoogleCloudPlatform/data-to-ai/blob/main/notebooks/part_2_large_scale_understanding.ipynb">
#     <img width="32px" src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg" alt="GitHub logo"><br> View on GitHub
#   </a>
# </table>

# %% [markdown] id="ktNVdhAwkEjP"
# ## Note
#
# Because this notebook involves large amounts of data (thousands of images), **some of the steps may take several minutes to complete**. If you are demonstrating these capabilities in a live setting, you may want to pre-run some of these steps.
#
# ## Overview
#
# This notebook is the second part of the CleanSight example application. Whereas Part 1 represents an operational system that ingests and processes bus stop images as they arrive, this notebook focuses on the large-scale AI capabilities available once a large number of images has been collected.
#
# Moreover, this notebook will compare the different **embedding models** and **vector search** methods to help you determine which is right for your use case.
#
# If you have not already, run the Part 1 notebook which will set up some required infrastructure and resources. Where possible, the same buckets, connections, and other resources are re-used from the Part 1 notebook.

# %% id="h_KvYlGg5DzS"
%pip install --upgrade --user google-cloud-aiplatform

# %% id="ZJl4dZ6FurrZ"
from IPython.display import HTML, display
import pandas as pd

PROJECT_ID = "<your project>" # @param {type:"string"}
REGION = "us-central1" # @param {type:"string"}
BQ_DATASET = "multimodal"

if PROJECT_ID == "<your project>":
  PROJECT_ID = !gcloud config get-value project
  PROJECT_ID = PROJECT_ID[0]

BUCKET_NAME = f"{PROJECT_ID}-multimodal"
SOURCE_PATH = f"gs://{BUCKET_NAME}/sources"
TARGET_PATH = f"gs://{BUCKET_NAME}/target"
USER_AGENT = "cloud-solutions/data-to-ai-nb-usage-v1"

PROJECT_ID


# %% id="akXiqbzSaPGX"
def preview_image(url):
  if pd.notna(url):
    return f'<img src="{url}" style="width:400px; height:auto; transition: transform 0.25s ease; border: 1px solid black;" onmouseover="this.style.transform=\'scale(1.5)\';" onmouseout="this.style.transform=\'scale(1.0)\';">'
  else:
    return None


# %% [markdown] id="Z00JYZJpr0QC"
# ## 1. Import full sample collection and extend schema
#
# This step will copy over 5,000 bus stop images into your bucket, and will take 3-5 minutes. This is a collection of synthetic images based on real bus stop photos. They have been edited in an automated process using Gemini and Imagen to produce our example dataset.

# %% id="IgrqaYJZuWV4"
!gcloud storage cp -r gs://bus-stops-open-access/edited-images/* {TARGET_PATH}

# %% [markdown] id="L299q0U_a-uj"
# Additionally, we want to analyze and store a few additional details about each bus stop for future search and analysis, and so we'll extend the `image_reports` table.

# %% id="vithtzMiaHF6"
%%bigquery

ALTER TABLE `multimodal.image_reports` ADD COLUMN cleanliness_description STRING;
ALTER TABLE `multimodal.image_reports` ADD COLUMN safety_description STRING;

# %% [markdown] id="vJC_sSpK3DVj"
# ## 2. Generate image reports

# %% [markdown] id="d-Kfuj0o1S5s"
# Now let's revisit the table `image_reports`. For each image in the object table `objects`, we want to **enrich** the image record with generic text description, safety rating, cleanliness rating, and descriptions of the safety/cleanliness observations for later retreival and analysis.
#
# The Part 1 notebook showed how to perform this inside BigQuery. Here in Part 2, the following code section will show how you would do this in Python using [controlled generation](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output).

# %% id="dnM0oWfz2_EG"
import vertexai
from vertexai import generative_models
from vertexai.generative_models import GenerationConfig, GenerativeModel, Part, Image

# %% id="gSDkQfX83UFW"
image_reports_prompt_text = """
  You are given an image of a bus stop. Analyze the image and provide the following:
    - a brief, generic description of the bus stop and its surroundings
    - count the number of people visible in the image
    - a rating of the cleanliness on a scale of 1 to 3 inclusive, where 3 indicates perfectly clean, and 1 indicates dirty and/or poor overall condition.
    - a rating of the safety of the bus stop on a scale of 1 to 3 inclusive, where 3 indicates no safety concerns, and 1 indicates unsafe conditions.
    - briefly describe cleanliness of the bus stop and its overall condition
    - briefly describe any safety concerns apparent in the image, such as low-hanging power lines, snow or ice, or vehicles in the loading area.
"""

response_schema = {
    'type': 'object',
    'properties': {
        'description': {
            'type': 'string'
        },
        'number_of_people': {
            'type': 'integer'
        },
        'cleanliness_level': {
            'type': 'integer'
        },
        'safety_level': {
            'type': 'integer'
        },
        'cleanliness_description': {
            'type': 'string'
        },
        'safety_description': {
            'type': 'string'
        }
    }
}
generation_config = GenerationConfig(
    candidate_count=1,
    max_output_tokens=1024,
    response_mime_type='application/json',
    response_schema=response_schema
)

model = GenerativeModel(model_name='gemini-2.0-flash-lite-001', generation_config=generation_config)

# %% id="mnGIWSqv3gcq"
from google.cloud import bigquery, storage
from google.api_core.client_info import ClientInfo
import time, json, pprint

client = bigquery.Client(client_info=ClientInfo(user_agent=USER_AGENT))

ot_sql = f'select * from `multimodal.objects` order by updated desc limit 1'
query_job = client.query(ot_sql)
rows = query_job.result()

for i, image in enumerate(rows):
  # including small delay to avoid potential quota issues
  time.sleep(3)

  image_metadata = { m['name']:m['value'] for m in image.metadata }
  if 'image_gen_prompt' in image_metadata:
    image_metadata.pop('image_gen_prompt')
  if 'source_image_uri' in image_metadata:
    image_metadata.pop('source_image_uri')

  prompt_image = Part.from_uri(image.uri, image.content_type)

  prompt = [image_reports_prompt_text, prompt_image]
  try:
    response = model.generate_content(prompt)
    json_response = json.loads(response.text)

    bq_row = { **json_response, **image_metadata }

    # the Gemini response schema and the object metadata mostly match our table,
    # but we still need to rename and/or remove a couple things
    bq_row['updated'] = bq_row.pop('event_date') + " 00:00"
    bq_row['report_id'] = bq_row.pop('image_id')
    bq_row['uri'] = image.uri

    pprint.pp(bq_row)

    # if you're using a script like this to generate data, this is where you
    # might insert the synthetic record into the BQ table.
    #client.insert_rows_json(client.get_table('multimodal.image_reports'), [bq_row])

  except Exception as e:
    print(e)


# %% [markdown] id="FBGqU4eTroVz"
# **Of course**, we're working with over 5,000 images of bus stops and don't have time here to generate descriptions and ratings for all of them in this demo. So, we've pre-generated the `bus_stops` and `image_reports` tables that you can load in directly.
#
# A new table in this notebook, `bus_stops`, represents the physical bus stop with an address and a geographic location. Each record in `image_reports` is associated with a `bus_stop`.

# %% id="qH-R3dQZsA-5"
%%bigquery

LOAD DATA OVERWRITE `multimodal.bus_stops`
FROM FILES (
  format = 'NEWLINE_DELIMITED_JSON',
  json_extension = 'GEOJSON',
  uris = ['gs://bus-stops-open-access/loader-data/bus_stops000000000000.json']);

LOAD DATA OVERWRITE `multimodal.image_reports`
FROM FILES (
  format = 'JSON',
  uris = ['gs://bus-stops-open-access/loader-data/image_reports_g15.json']);

-- match the URIs in the sample data to those in our local object table
UPDATE `multimodal.image_reports` report
SET uri = obj.uri
FROM `multimodal.objects` obj
WHERE report_id = (select value from unnest(metadata) where name='image_id');

SELECT count(*) from `multimodal.image_reports`;

# %% [markdown] id="ByNWlGJrvLc2"
# # 3. Create text and multimodal embeddings
#
# Here we are reprising the "Semantic Similar Search" section of the Part 1 notebook -- except this time, we have enough data needed to build a proper BigQuery vector index!
#
# Again we'll start by generating embeddings for each report description, and store them in the `image_reports_vector_db` table.
#
# This step will take approximately 60 seconds to complete on our 5,000+ image table.

# %% id="WmSq3RJWvjY7"
%%bigquery
CREATE OR REPLACE TABLE `multimodal.image_reports_vector_db` AS (
SELECT
  report_id, uri, bus_stop_id, content as description,
  cleanliness_level, safety_level,
  ml_generate_embedding_result AS embedding,
  ml_generate_embedding_status AS status
FROM
  ML.GENERATE_EMBEDDING(
    MODEL `multimodal.text_embedding_model`,
    (SELECT * EXCEPT(description), description as content FROM `multimodal.image_reports` WHERE description IS NOT NULL),
    STRUCT('SEMANTIC_SIMILARITY' as task_type)
  )
);

# %% id="twwzEWDRvW7Q"
%%bigquery

CREATE VECTOR INDEX reports_text_index ON `multimodal.image_reports_vector_db`(embedding)
STORING (report_id, uri, bus_stop_id, description, cleanliness_level, safety_level)
OPTIONS (index_type = 'IVF', distance_type = 'COSINE')

# %% [markdown] id="tBIhoFMz16Hl"
# **Now, for something a little different...**
#
# Instead of 1) generating text descriptions and then 2) generating text embeddings, we can generate **multimodal** embeddings directly from the object table using the [`multimodalembedding`](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/multimodal-embeddings-api) model.
#
# Let's do this, and then we can compare and contrast searches between the two approaches.

# %% id="bEwpUdbG149k"
%%bigquery

CREATE OR REPLACE MODEL `multimodal.mm_embedding_model`
REMOTE WITH CONNECTION `us-central1.multimodal`
OPTIONS ( endpoint = 'multimodalembedding@001')

# %% [markdown] id="G-M-EvYB5lSX"
# **NOTICE** the `LIMIT 1` at the end of the following query. This is an example for how you would generate multimodal embeddings directly from an object table. Since there are 5000+ images in our object table, this query could take a long time (5-10 minutes).
#
# If you want to see it run for yourself, remove the `LIMIT` and run it. Otherwise, run this cell as-is and proceed to the next cell to load a pre-made table.

# %% id="KgpdTFQN4zJz"
%%bigquery

CREATE OR REPLACE TABLE `multimodal.image_reports_vector_mm_db` AS
SELECT * FROM
  ML.GENERATE_EMBEDDING(
    MODEL `multimodal.mm_embedding_model`,
    (SELECT * FROM `multimodal.objects`
    LIMIT 1)
  )

# %% id="E0UbdNaT_mZe"
%%bigquery

LOAD DATA OVERWRITE `multimodal.image_reports_vector_mm_db`
FROM FILES (
  format = 'JSON',
  uris = ['gs://bus-stops-open-access/loader-data/image_reports_vector_mm_db.json']);

-- match the URIs in the sample data to those in our local image_reports table
UPDATE `multimodal.image_reports_vector_mm_db` vdb
SET uri = reports.uri
FROM (select report_id, uri from `multimodal.image_reports` group by report_id, uri) reports
WHERE report_id = (select value from unnest(vdb.metadata) where name='image_id');

CREATE OR REPLACE VECTOR INDEX reports_text_index ON `multimodal.image_reports_vector_mm_db`(ml_generate_embedding_result)
OPTIONS (index_type = 'IVF', distance_type = 'COSINE');

# %% [markdown] id="S-71V-7eADSi"
# #4. Using text and multimodal embeddings for search and analysis
#
# Let's recap where we stand currently:
# 1. We created the `image_reports` table, which contains generated descriptions of the images from the objects table (`multimodal.objects`)
# 2. We then created `image_reports_vector_db` from embeddings generated from those descriptions.
# 3. Separately, we created  the `image_reports_vector_mm_db` by generating multimodal embeddings directly from the object table.
#
# In the previous notebook, we focused on the use case of a transit agency who wants to maintain the cleanliness of its bus stops. Here, we'll explore anadditional use case that leverages the increased volume of data we have available.

# %% [markdown] id="jY-DoPTGd-cP"
# ## Use case: Ad Verification
#
# As a marketer, if I buy an ad on a bus stop, I want to verify that it was actually displayed according to my requirements during the time period I expect.
#
# The transit agency collecting these images should be able to quickly prove to their marketing partner that their ad was indeed shown to riders at the bus stop.
#
# ### Base Identification
#
# As an example of this, the query below searches for all bus stops that display an advertisement for Burger King. The marketer can then check these timestamped images against their ad buys to verify that the ad was in service during the contracted period.

# %% id="fRMG7LiXFAvn"
%%bigquery df1

SELECT
  base.updated,
  CONCAT("https://storage.mtls.cloud.google.com/", SPLIT(base.uri, "gs://")[OFFSET(1)]) AS url,
FROM
  VECTOR_SEARCH(
    TABLE `multimodal.image_reports_vector_mm_db`,
    'ml_generate_embedding_result',
    (SELECT * FROM ML.GENERATE_EMBEDDING(
      MODEL `multimodal.mm_embedding_model`,
      (SELECT 'bus stop has an ad for Burger King' AS content)
    )),
    'ml_generate_embedding_result',
    top_k => 3);

# %% [markdown] id="npv8Om7Dcq6w"
# Before we look at the results, it's worth taking a step back to note just how ***fast*** that query ran! The generated embeddings combined with the `VECTOR INDEX` enable us to search over vast collections of varied and complex imagery in no time at all.

# %% id="eiuQsGWFYfiR"
df1['image'] = df1['url'].apply(preview_image)
HTML(df1[['updated', 'image']].to_html(escape=False))

# %% [markdown] id="hyo03_i2h1Sj"
# ### Quality Verification
#
# Using `VECTOR_SEARCH`, we're able to identify which bus stops are displaying the queried advertisement. Now, let's take this one step further.
#
# Mere identification may not be enough to prove to an advertiser that their ad is displayed in the proper manner. What if the ad is damaged? What if it is being displayed in poor conditions, such as in a bus stop that is dirty or unsafe?
#
# As an advertiser, I want to make sure my product or service is being marketed under the best possible conditions. So, let's try to search the previous resultset for potential issues.
#
#

# %% id="G3KHDdVTryB-"
%%bigquery df2

SELECT
  base.updated,
  CONCAT("https://storage.mtls.cloud.google.com/", SPLIT(base.uri, "gs://")[OFFSET(1)]) AS url,
FROM
  VECTOR_SEARCH(
    TABLE `multimodal.image_reports_vector_mm_db`,
    'ml_generate_embedding_result',
    (SELECT * FROM ML.GENERATE_EMBEDDING(
      MODEL `multimodal.mm_embedding_model`,
      (SELECT 'bus stop has an ad for Burger King AND ALSO contains cleanliness issue such as litter or trash' AS content)
    )),
    'ml_generate_embedding_result',
    top_k => 1);

# %% id="n3XFAYy6sARR"
df2['image'] = df2['url'].apply(preview_image)
HTML(df2[['updated', 'image']].to_html(escape=False))

# %% [markdown] id="AZislxSWvoIS"
# Clearly, such an unclean bus stop would not meet the requirements of a reasonable advertiser. In a real business setting, the advertiser would have grounds to request that the transit agency invest in cleaning up the dirty areas. This would result in a **win-win** for everyone -- the advertiser, the transit agency, and bus riders!

# %% [markdown] id="ziuSAZy29uyz"
# # Use Case: Weather Report
#
# Ok, great -- we can verify that ads are running, and we can assess the quality of those ad displays.
#
# Another factor that affects the economics of advertising and transit ridership is of course, **the weather**! As a transit agency, I want to understand how weather affects the usage of my bus stops.
#
# All weather events have two identifiable components: a **time** and a **location**.
#
# In our data model, we can match up weather events using `image_reports.updated` as our time, and `bus_stop.geom`.
#
# For the next section, we'll be using a historic storms dataset from NOAA that is available in the BigQuery public datasets program. In order to proceed, let's copy that table into our local BigQuery dataset.

# %% id="MW5ExsabIbVR"
!bq cp -f -n bigquery-public-data:noaa_historic_severe_storms.storms_2024 $PROJECT_ID:multimodal.storms

# %% [markdown] id="io6hFoxAfv-1"
# Let's first do some exploration. Run the following query to see which bus stops have been most affected by severe weather events in the past year.

# %% id="ioftsms0fvkm"
%%bigquery

SELECT
  bus_stop_id,
  count(*) as occurrences
  FROM `multimodal.bus_stops` stops

INNER JOIN `multimodal.storms` storms
  ON (
    ST_INTERSECTS(stops.geometry, ST_BUFFER(storms.event_point, 5000))
  )
group by bus_stop_id
order by occurrences desc

# %% [markdown] id="7V56WZYxgDF0"
# Looks like just about every bus stop experience some kind of severe weather event -- but some are definitely more affected than others!
#
# An understanding of which bus stations are most affected by weather can be useful for scheduling maintenance and making sure that the station and all the attendant infrastructure are in good working order.

# %% [markdown] id="mR3zeZiNoKUl"
# To observe particular instances of severe weather at that bus stop over time, we can revisit `VECTOR_SEARCH` and combine it with our `storm` table to corroborate recorded weather events with observed images.
#
# The following is an example query that combines the vector search and the spatio-temporal join against historical weather events; you can play around with this query and modify for your own use case.

# %% id="Obqfb7C5gezO"
%%bigquery df3

WITH severe_weather_reports AS (
  SELECT
    base.updated,
    base.uri,
    distance,
    CONCAT("https://storage.mtls.cloud.google.com/", SPLIT(base.uri, "gs://")[OFFSET(1)]) AS url
  FROM
    VECTOR_SEARCH(
      TABLE `multimodal.image_reports_vector_mm_db`,
      'ml_generate_embedding_result',
      (SELECT * FROM ML.GENERATE_EMBEDDING(
        MODEL `multimodal.mm_embedding_model`,
        (SELECT 'bus stop appears affected by snow, wind, hail, or is otherwise damaged in some way' AS content)
      )),
      'ml_generate_embedding_result',
      top_k => 5)
)
SELECT
  distinct(reports.bus_stop_id) as bus_stop_id,
  reports.updated,
  event_type,
  url,
  distance
FROM `multimodal.image_reports` reports

INNER JOIN severe_weather_reports
  ON (severe_weather_reports.uri = reports.uri)

INNER JOIN `multimodal.bus_stops` stops
  ON (stops.bus_stop_id = reports.bus_stop_id)

INNER JOIN `multimodal.storms` storms
  ON (
    ST_INTERSECTS(stops.geometry, ST_BUFFER(storms.event_point, 10000))
  )
ORDER BY distance ASC
LIMIT 3

# %% id="G2a8FI3UgqLj"
df3['image'] = df3['url'].apply(preview_image)
HTML(df3[['bus_stop_id', 'updated', 'event_type', 'image']].to_html(escape=False))
