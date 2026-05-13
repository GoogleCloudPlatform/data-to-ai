# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.7
#   kernelspec:
#     display_name: Python 3
#     name: python3
# ---

# %% id="6MNyzDPuBBW_"
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

# %% [markdown] id="iY4DxOJqbcl6"
# # Synthetic Multimodal Data Generator
#
# This notebook shows how to synthesize data for multimodal analytics use cases, and is used to generate the data used in the CleanSight example application.
#
# This notebook is separate and distinct from the CleanSight application flow (parts 1-3).

# %% [markdown] id="j4K6s18ubuWG"
# ## Load and Anonymize Bus Stops
#
# Load bus stops from the National Transit database, and anonymize their addresses.

# %% id="5jw1PmTQ4ReT"
PROJECT_ID = "<your project>" # @param hide {type:"string"}
LOCATION = "us-central1" # @param {type:"string"}

BUCKET = 'bus-stops-open-access' # @param {type:"string"}

BQ_DATASET = 'bus_d2ai'
BQ_TABLE = 'staging_ntd_stops'

STOP_FILE_URI = 'gs://bus-stops-open-access/loader-data/NTAD_National_Transit_Map_Stops_6633473857343365838.csv' # @param {type:"string"}

# %%
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
# Test Change
# 1. load ntd stop data

ntd_stops_schema = [
    SchemaField('OBJECTID', 'INT64'),
    SchemaField('ntd_id', 'STRING'),
    SchemaField('stop_id', 'STRING'),
    SchemaField('stop_name', 'STRING'),
    SchemaField('stop_desc', 'STRING'),
    SchemaField('stop_lat', 'FLOAT'),
    SchemaField('stop_lon', 'FLOAT'),
    SchemaField('zone_id', 'STRING'),
    SchemaField('stop_url', 'STRING'),
    SchemaField('stop_code', 'STRING'),
    SchemaField('location_type', 'STRING'),
    SchemaField('parent_station', 'STRING'),
    SchemaField('stop_timezone', 'STRING'),
    SchemaField('wheelchair_boarding', 'STRING'),
    SchemaField('level_id', 'STRING'),
    SchemaField('platform_code', 'STRING'),
    SchemaField('agency_id', 'STRING'),
    SchemaField('download_date', 'STRING'),
    SchemaField('x', 'FLOAT'),
    SchemaField('y', 'FLOAT')
]

try:
    print(f'creating bq client with {PROJECT_ID} {LOCATION}')
    bigquery_client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    dataset = bigquery.Dataset(f'{PROJECT_ID}.{BQ_DATASET}')
    dataset.location = LOCATION

    bigquery_client.create_dataset(dataset, timeout=30)

    dataset_ref = bigquery_client.dataset(BQ_DATASET)
    table_ref = dataset_ref.table(BQ_TABLE)

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=ntd_stops_schema,
    )
    load_job = bigquery_client.load_table_from_uri(
        STOP_FILE_URI, table_ref, job_config=job_config
    )
    load_job.result()

    print('created {}.{}'.format(BQ_DATASET, BQ_TABLE))

except Exception as e:
    print('ntd_stop load failed {}'.format(e))

# 2. select into bus stop data model

from google.cloud import storage

## 2a. anonymize bus stop addresses by replacing them with generated street
## numbers and animal names as the street names
ANIMALS_PATH = 'loader-data/animals.txt' # @param {type:"string"}
address_suffixes = ['Circle', 'Square', 'Road', 'Lane', 'Street', 'Avenue', 'Way']

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET)
blob = bucket.blob(ANIMALS_PATH)
animals_text = blob.download_as_string().decode("utf-8")

animals = animals_text.splitlines()

# this query generates bus stops from the NTD dataset and does the following:
# - anonymizes street names using the animals list and random street numbers
# - randomly decides values for school_zone, seating, and other boolean fields
# - uses st_clusterdbscan() to generate bus_line_ids for bus_stops that are near
#   each other
# - convert the stop_lon and stop_lat values into a GEOGRAPHY type using st_geogpoint()

create_bus_stops_query = f"""
  declare animals array <string>;
  declare suffixes array <string>;

  set animals = {animals};
  set suffixes = {address_suffixes};

  create or replace table `{PROJECT_ID}.{BQ_DATASET}.bus_stops` as (
    select
      row_number() over() as bus_stop_id,
      *
    from (
      select
        cast((st_clusterdbscan(st_geogpoint(stop_lon, stop_lat), 200, 3) OVER()) as int64) as bus_line_id,
        mod(OBJECTID, 10) as stop_num,
        concat(
            cast(rand() * 10000 as int64),
            ' ', animals[cast(rand() * (array_length(animals) - 1) as int64)],
            ' ', suffixes[cast(rand() * (array_length(suffixes) - 1) as int64)]
        ) as street_address,
        (rand() > 0.9) as school_zone,
        (rand() > 0.6) as seating,
        -1 as num_benches,
        (rand() > 0.5) as maps,
        (rand() > 0.5) as shelter_ads,
        '' as panel_type,
        (rand() > 0.2) as lighting,
        st_geogpoint(stop_lon, stop_lat) as geom
      from `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`)
      where bus_line_id is not null
  )
"""

# this will generate a new bus_stop record for each of the 65k+ bus stops in the NTD
# dataset and store in a BQ table, minus the stops that were too far away from the
# others to be part of a bus_line. resulting table will have about 50k rows
try:
  client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
  query_job = client.query(create_bus_stops_query)
  results = query_job.result()

except Exception as e:
  print('bus_stop create failed {}'.format(e))



# %% [markdown] id="uI8FPLcScCbb"
# ## Generate Bus Lines
#
# Bus "lines", or routes, aren't used much in our example application, but you can imagine that they would be very important in a real transit application because they would define the stops a particular bus visits, and in which order they are visited.
#
# This cell uses the values created by `st_clusterdbscan` above as the unique IDs for bus lines to be created.

# %% id="CqZErlb5cCua"
# 3. generate a bus_line for each bus_stop cluster

PLANTS_PATH = 'loader-data/plants.txt' # @param {type:"string"}
line_suffixes = ['Route', 'Line', 'Express']

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET)
blob = bucket.blob(PLANTS_PATH)

# in the NTD dataset, many bus routes are named after the street or neighborhood
# they are located in. We use plant names to anonymize these in the same way we
# used animal names in the previous cell to anonymize bus stop streets.
plants_text = blob.download_as_string().decode("utf-8")
plants = plants_text.splitlines()

create_bus_lines_query = f"""
  declare plants array <string>;
  declare suffixes array <string>;

  set plants = {plants};
  set suffixes = {line_suffixes};

  create or replace table `{PROJECT_ID}.{BQ_DATASET}.bus_lines` as (
    select
      bus_line_id,
      concat(
        plants[cast(rand() * (array_length(plants) - 1) as int64)],
        ' ', suffixes[cast(rand() * (array_length(suffixes) - 1) as int64)]
      ) as name,
      min(bus_stop_id) as start_bus_stop,
      max(bus_stop_id) as end_bus_stop,
      count(distinct bus_stop_id) as num_stops
    from `{PROJECT_ID}.{BQ_DATASET}.bus_stops`

    group by bus_line_id
  )
  """
try:
  client = bigquery.Client()
  query_job = client.query(create_bus_lines_query)
  results = query_job.result()

except Exception as e:
  print('bus_line create failed {}'.format(e))



# %% [markdown] id="i3myflHccaW8"
# ## Generate Bus Stop Images
#
# From a small intial set of real photos, you can use Imagen to create variants of those photos based on the prompts you provide. For example, you can instruct Imagen to add snow or people to the bus stop in order to evaluate a wider variety of situations.
#
# `DEMO_MODE` is an optional flag that can be used to generate a smaller subset of data. Leave this unchecked.

# %% id="QVw4tDKVcz7q"
SOURCE_FOLDER = 'source-images'
EDITED_FOLDER = 'edited-images'
DEMO_MODE = False # @param {type:"boolean"}
DEMO_RANGE = 3 # used to determine % of prompts and number of images to process
DEFAULT_RANGE = 100 # used to determine % of prompts

# %% [markdown] id="7PbJAjeSc_hj"
# ### Object tables
#
# This process also makes use of object tables; you can either create a new connection, or re-use the existing connection that you already have from the CleanSight application.

# %% id="-vDagGzKc0Ay"
# !bq mk --connection --location=$LOCATION \
#     --connection_type=CLOUD_RESOURCE gcs_stop_images_cxn

# %% id="hWKaNL2FdK4z"
from google.cloud import bigquery

BQ_SOURCE_TABLE = 'source_stop_images_ot'
BQ_EDITED_TABLE = 'edited_stop_images_ot'

source_object_table_sql = f"""
  create or replace external table `{PROJECT_ID}.{BQ_DATASET}.{BQ_SOURCE_TABLE}`
  with connection `{PROJECT_ID}.{LOCATION}.gcs_stop_images_cxn`
  options (
    object_metadata = 'SIMPLE',
    uris = ['gs://{BUCKET}/{SOURCE_FOLDER}/*']
  )
"""

edited_object_table_sql = f"""
  create or replace external table `{PROJECT_ID}.{BQ_DATASET}.{BQ_EDITED_TABLE}`
  with connection `{PROJECT_ID}.{LOCATION}.gcs_stop_images_cxn`
  options (
    object_metadata = 'SIMPLE',
    uris = ['gs://{BUCKET}/{EDITED_FOLDER}/*']
  )
"""

try:
  client = bigquery.Client()
  query_job = client.query(source_object_table_sql)
  query_job.result()

  query_job = client.query(edited_object_table_sql)
  query_job.result()

except Exception as e:
  print('object table creation failed {}'.format(e))

# get list of objects
client = bigquery.Client()

ot_sql = f'select * from `{PROJECT_ID}.{BQ_DATASET}.{BQ_SOURCE_TABLE}`'

if DEMO_MODE:
  ot_sql += f' LIMIT {DEMO_RANGE}'

query_job = client.query(ot_sql)
rows = query_job.result()

source_images = list(rows)
if DEMO_MODE:
  source_images = source_images[0:DEMO_RANGE]

print(len(source_images))

# %% id="f8I4_O40dkpu"
# %%bigquery

LOAD DATA OVERWRITE `bus_d2ai.bus_stop_image_mappings`
FROM FILES (
  format = 'JSON',
  uris = ['gs://bus-stops-open-access/loader-data/bus_stop_image_mappings.json']);

create or replace table bus_d2ai.image_gen_prompts (
  prompt_text string,
  prompt_type string
);

insert into bus_d2ai.image_gen_prompts (prompt_text, prompt_type) values
  ('add a low hanging power line in the bus stop area, making it difficult to get on and off the bus', 'Safety'),
  ('add a water leak in the bus stop area', 'Safety'),
  ('add construction zone and 1 construction vehicle in the bus stop area', 'Safety'),
  ('add a thick layer of snow covering the ground and partially covering the bus area', 'Safety'),
  ('add a small pile of garbage in the bus stop area', 'Cleanliness'),
  ('add graffiti on the side of the bus stop', 'Cleanliness'),
  ('add sleeping bag on bus bench', 'Cleanliness'),
  ('add 1 bottle of water, 1 bottle of juice, 1 can of beer to bus stop', 'Cleanliness'),
  ('add 1 person waiting for bus, either sitting or standing', 'People'),
  ('add 2 people waiting for bus, either sitting or standing', 'People'),
  ('add 3 people waiting for bus, one person sitting and the other two standing', 'People'),
  ('add 1-2 joggers passing by', 'People'),
  ('add a service dog with his owner', 'People'),
  ('add a construction worker', 'People'),
  ('add a billboard at the bus stop, advertising game day tickets', 'Advertisement'),
  ('add a billboard at the bus stop, advertising continuing education for adults', 'Advertisement'),
  ('add a billboard at the bus stop, advertising Burger King', 'Advertisement'),
  ('add a billboard at the bus stop, advertising Insomnia Cookies', 'Advertisement'),
  ('add a small collection of 5 small pieces of garbage scattered over a wide area', 'Augmentation'),
  ('add a small pile of garbage on the street', 'Augmentation'),
  ('add small shopping cart near the bus stop filled with junk', 'Augmentation'),
  ('add street cones in the bus stop area', 'Augmentation'),
  ('add trash can near bus stop area', 'Augmentation'),
  ('add a newspaper box next to the bus stop', 'Augmentation'),
  ('add 2-5 ebikes next to the bus stop', 'Augmentation'),
  ('add a yard sign with a public notice on it', 'Augmentation'),
  ('add a yard sign with a freeze warning', 'Augmentation'),
  ('change time of day to late evening', 'Augmentation'),
  ('change time of day to early morning', 'Augmentation'),
  ('change time of day to noon', 'Augmentation'),
  ('add a thick layer of snow covering the ground', 'Augmentation'),
  ('add thick layer of fog over bus stop area, reducing visibility', 'Augmentation');

# %% [markdown] id="PwqXA-wx-Zue"
# ## Generate a date range
#
# Photos are taken at a particular time and place. We know the places because the bus_stop table includes locations (longitude, latitude).  Here, we generate a range of times to attach to the image metadata.

# %% id="EhINIRVHdrrK"
from datetime import date, timedelta
import numpy as np

start_date = date(2025, 1, 1)
end_date = date(2025, 2, 15)
print("date range is " + str(start_date) + " - " + str(end_date))

dates_between = end_date - start_date
total_days = dates_between.days

def gen_random_dates(num_dates):
  randays = np.random.choice(total_days, num_dates, replace=False)
  results = [start_date + timedelta(days=int(day)) for day in randays]
  return results


# %% [markdown] id="fdwo8a_AdYn_"
# ## Use Imagen to generate photo variants
#
# **Please Note** as of March 2025 you need to fill out [this form](https://docs.google.com/forms/d/e/1FAIpQLScN9KOtbuwnEh6pV7xjxib5up5kG_uPqnBtJ8GcubZ6M3i5Cw/viewform) in order to get access to the Imagen model for editing in Vertex.
#
# The trick here is to use `SubjectReferenceImage` with `subject_description="bus stop"` in order to prime the model to know what it's supposed to be looking at. Then you can prompt it to make the edit by calling `_generate_images`, providing a `reference_images`, and it will generate a new image based on the original "subject" image.
#
# Iterating over the collection of input photos cross-joined with the list of prompts specificed above (in the `image_gen_prompts` table) quickly produces a large amount of data that can be used for analysis!

# %% id="ceUict04dZCK"
import vertexai

vertexai.init(project=PROJECT_ID, location=LOCATION)

from vertexai import generative_models
from vertexai.preview.vision_models import (
    ControlReferenceImage,
    Image,
    ImageGenerationModel,
    MaskReferenceImage,
    RawReferenceImage,
    SubjectReferenceImage
)

edit_model = ImageGenerationModel.from_pretrained('imagen-3.0-capability-001')

from google.cloud import storage
from google.cloud import bigquery
import uuid

storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET)

bq_client = bigquery.Client(location=LOCATION)

edited_images = []

for image_row in source_images:
  gcs_uri = image_row.uri
  image_name = gcs_uri.split('/')[4].split('.')[0]
  print('processing', image_name)

  # look up the bus stop id
  bus_stop_id = None
  sql = f"select bus_stop_id from bus_d2ai.bus_stop_image_mappings where image_name = '{image_name}'"
  rows = bq_client.query_and_wait(sql)
  for row in rows:
    bus_stop_id = row[0]

  if bus_stop_id == None:
    sql = f"select bus_stop_id from bus_d2ai.bus_stop_image_mappings where image_name is null order by bus_stop_id limit 1"
    rows = bq_client.query_and_wait(sql)
    for row in rows:
      bus_stop_id = row[0]

    if bus_stop_id == None:
      print('Error finding available bus stop id')
      quit()

    sql = f"update bus_d2ai.bus_stop_image_mappings set image_name = '{image_name}' where bus_stop_id = {bus_stop_id}"
    bq_client.query_and_wait(sql)

  print(f'bus_stop_id {bus_stop_id} assigned to {image_name}')

  # retrieve some number of prompts by sampling the image_gen_prompts table
  image_prompts = []
  if DEMO_MODE:
    sql = f"select prompt_text from bus_d2ai.image_gen_prompts tablesample system ({DEMO_RANGE} percent)"
  else:
    sql = f"select prompt_text from bus_d2ai.image_gen_prompts tablesample system ({DEFAULT_RANGE} percent)"

  rows = client.query_and_wait(sql)

  for row in rows:
    image_prompts.append(row[0])
  print(f'retrieved {len(image_prompts)} image_prompts:', image_prompts)

  # generate random event dates within a date range
  # want the number of event dates to equal the number of prompts
  num_dates = len(image_prompts)
  event_dates = gen_random_dates(num_dates)
  print(f'generated {len(event_dates)} event_dates:', event_dates)

  for i, prompt in enumerate(image_prompts):

    event_date = str(event_dates[i])

    try:
      ref_image = Image(gcs_uri = gcs_uri)
      raw = RawReferenceImage(image=ref_image, reference_id=1)

      subject = SubjectReferenceImage(image=ref_image, reference_id=1, subject_type='default',  subject_description='bus stop')

      print(f'generating variants for source image {gcs_uri}...')
      edited_image_response = edit_model._generate_images(
          prompt=prompt,
          reference_images=[subject],
          number_of_images=1,
          safety_filter_level='block_few',
          person_generation='allow_adult',
          aspect_ratio='4:3'
      )

      edited_image_metadata = {
          'source_image_uri': gcs_uri,
          'image_gen_prompt': prompt,
          'bus_stop_id': bus_stop_id,
          'event_date': event_date
      }
      for edited_image in edited_image_response:
        edited_image_id = str(bus_stop_id) + '-' + ''.join(str(uuid.uuid4()).split('-')[0:3])
        edited_image_name = f'{edited_image_id}.jpg'
        edited_image_metadata.update({ 'image_id': edited_image_id })

        blob = bucket.blob(f'{EDITED_FOLDER}/{event_date}/{edited_image_name}')
        blob.metadata = edited_image_metadata
        blob.upload_from_string(edited_image._image_bytes, "image/jpg")
        print(f'Uploaded edited image {edited_image_name} generated from source image {gcs_uri}')

    except Exception as e:
      print('image generation or upload failed; skipping {}'.format(e))


