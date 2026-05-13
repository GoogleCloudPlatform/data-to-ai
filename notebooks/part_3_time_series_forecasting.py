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
#     language: python
#     name: python3
# ---

# %% id="lvNpj26L7bbY67xWsvugZull"
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

# %% [markdown] id="g4xlhet9alul"
# # CleanSight (Part 3): Predictions of bus stop related events
# *powered by BigQuery and Gemini*

# %% [markdown] id="1tE-f4hma-QX"
# <table align="left">
# <td style="text-align: center">
#   <a href="https://colab.research.google.com/github/GoogleCloudPlatform/data-to-ai/blob/main/notebooks/part_3_time_series_forecasting.ipynb">
#     <img width="32px" src="https://www.gstatic.com/pantheon/images/bigquery/welcome_page/colab-logo.svg" alt="Google Colaboratory logo"><br> Open in Colab
#   </a>
# </td>
# <td style="text-align: center">
#   <a href="https://console.cloud.google.com/vertex-ai/colab/import/https:%2F%2Fraw.githubusercontent.com%2FGoogleCloudPlatform%2Fdata-to-ai%2Fmain%2Fnotebooks%2Fpart_3_time_series_forecasting.ipynb">
#     <img width="32px" src="https://lh3.googleusercontent.com/JmcxdQi-qOpctIvWKgPtrzZdJJK-J3sWE1RsfjZNwshCFgE_9fULcNpuXYTilIR2hjwN" alt="Google Cloud Colab Enterprise logo"><br> Open in Colab Enterprise
#   </a>
# </td>
# <td style="text-align: center">
#   <a href="https://console.cloud.google.com/vertex-ai/workbench/deploy-notebook?download_url=https://raw.githubusercontent.com/GoogleCloudPlatform/data-to-ai/main/notebooks/part_3_time_series_forecasting.ipynb">
#     <img src="https://www.gstatic.com/images/branding/gcpiconscolors/vertexai/v1/32px.svg" alt="Vertex AI logo"><br> Open in Vertex AI Workbench
#   </a>
# </td>
# <td style="text-align: center">
#   <a href="https://console.cloud.google.com/bigquery/import?url=https://github.com/GoogleCloudPlatform/data-to-ai/blob/main/notebooks/part_3_time_series_forecasting.ipynb">
#     <img src="https://www.gstatic.com/images/branding/gcpiconscolors/bigquery/v1/32px.svg" alt="BigQuery Studio logo"><br> Open in BigQuery Studio
#   </a>
# </td>
# <td style="text-align: center">
#   <a href="https://github.com/GoogleCloudPlatform/data-to-ai/blob/main/notebooks/part_3_time_series_forecasting.ipynb">
#     <img width="32px" src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg" alt="GitHub logo"><br> View on GitHub
#   </a>
# </table>

# %% [markdown] id="M6SimqgxbcmM"
# # Overview
#
# This notebook is a continuation of the demo of BigQuery capabilities in a fictional project called **CleanSight**. We'll explore how advanced time-series predictions can be combined with data produced using multimodal analysis.
#
# This notebook will highlight:
#
# * Forecasting expected number of riders for a particular bus stop based on the BigQuery's multiple time-series with univariate and multivariate models.
# * Using [WeatherNext 2](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/weathernext-2/) BigQuery dataset for creating time-series models and for forecasting based on the predicted weather.
#
# Let's get started!

# %% [markdown] id="hLx6XOQbj-NP"
# # Prerequisites

# %% [markdown] id="l40wdqdEkIlC"
# The sample code below assumes you have access to the [WeatherNext 2](https://developers.google.com/weathernext/guides/bigquery) BigQuery dataset. Please review the terms and conditions of using this data.
#
# If you don't have access to the WeatherNext data you can still forecast rideship using a univariate model.

# %% [markdown] id="ACfseMUMlvmv"
# ## WeatherNext Graph dataset

# %% [markdown] id="9Wy1OQNpl3cA"
# There are two BigQuery datasets - one with 64 ensembles and one with precalculated mean values of these ensambles. We are going to use the [latter one](https://console.cloud.google.com/bigquery/analytics-hub/discovery/projects/gcp-public-data-weathernext/locations/us/dataExchanges/weathernext_19397e1bcb7/listings/weathernext2_mean_19dbf307dec) for the forecasting - it is much easier, and cheaper, to use. Once you get access, a linked dataset named `weathernext_2_mean` will be created in your Google Cloud project.
#
# The dataset will contain one table: `weathernext_2_0_0_mean`. This table gets updated 4 times a day with newly forecasted data. The data is forecast for a particular rectangular geographic area. The forecast is done in 6 hour intervals and a number of data points are included: expected temperatures at different levels above ground, wind, humidity, etc.

# %% [markdown] id="TJNbPGBEgQKC"
# ## Getting started

# %% [markdown] id="ERSjkLhkgRu9"
# Let's first set up some environment variables, including your Google Cloud project ID and the region to deploy resources into.
#
# This notebook assumes that the WeatherNext dataset was created in the same project. If you would like to use a different project, some of the SQL statements will need to be modified to include the project ID of the project which hosts the WeatherNext dataset.

# %% id="UbBMzAcsgaOW"
PROJECT_ID = "" # @param {type:"string"}
REGION = "us-central1" # @param {type:"string"}

if PROJECT_ID == "":
  PROJECT_ID = !gcloud config get-value project
  PROJECT_ID = PROJECT_ID[0]

# %% [markdown] id="HjmqxYLZgs5_"
# ### Enable necessary APIs

# %% id="T5kAeQ5vgvs0"
!gcloud services enable --project {PROJECT_ID} \
  bigquery.googleapis.com \
  aiplatform.googleapis.com

# %% [markdown] id="mm46iiNJg-Oj"
# ### Install packages

# %% id="PWQI4caghEpz"
%pip install --upgrade --user --quiet \
    google-cloud-aiplatform \
    google-cloud-bigquery

# %% [markdown] id="7yLx_qY8ZHG3"
# ### Create visualization helper functions
#

# %% id="AQmMdxj0ZLOe"
import matplotlib.pyplot as plt
import pandas as pd

def display_columns_as_rows(data):
  display_data = data.transpose()
  styler = display_data.style
  styler.set_table_styles([
    {'selector': 'th.col_heading', 'props': 'text-align: right;'},
    {'selector': 'th.row_heading', 'props': 'text-align: right;'},
    {'selector': 'td', 'props': 'text-align: right;'},
    ], overwrite=False)
  display(styler)

def plot_historical_and_forecast(title,
                                 historical_data,
                                 timestamp_col_name,
                                 data_col_name,
                                 temperature_col_name=None,
                                 percipitation_col_name=None,
                                 forecast_output=None,
                                 forecast_temperature=None,
                                 actual=None):

    historical_data = historical_data.sort_values(timestamp_col_name)

    display_weather_graphs = temperature_col_name is not None

    figure = plt.figure(figsize=(20, 14 if display_weather_graphs else 6))
    # plt.xlabel('Date and time')

    if display_weather_graphs:
      plt.tick_params(left = False, bottom = False, labelleft = False, labelbottom = False)

      temperature_axis = plt.subplot(312)
      plt.ylabel('Temperature (K)')
      plt.plot(historical_data[timestamp_col_name], historical_data[temperature_col_name], color='orange', label='Temperature')
      plt.legend(loc = 'upper center', prop={'size': 14})
      temperature_axis.tick_params(bottom = False, labelbottom = False)

      percipitation_axis = plt.subplot(313, sharex = temperature_axis)
      plt.ylabel('Percipitation (m)')
      plt.plot(historical_data[timestamp_col_name], historical_data[percipitation_col_name], color='green', label = 'Precipitation')
      plt.legend(loc = 'upper center', prop={'size': 14})

      main_axis = plt.subplot(311, sharex = temperature_axis)
      main_axis.tick_params(bottom = False, labelbottom = False)

    # Plot the input historical data
    plt.ylabel('Number of riders')
    plt.plot(historical_data[timestamp_col_name], historical_data[data_col_name], label = 'Historical')


    if forecast_output is not None:
        forecast_output = forecast_output.sort_values('forecast_timestamp')
        forecast_output['forecast_timestamp'] = pd.to_datetime(forecast_output['forecast_timestamp'])
        x_data = forecast_output['forecast_timestamp']
        y_data = forecast_output['forecast_value']
        confidence_level = forecast_output['confidence_level'].iloc[0] * 100
        low_CI = forecast_output['prediction_interval_lower_bound']
        upper_CI = forecast_output['prediction_interval_upper_bound']
        # Plot the forecast data
        plt.plot(x_data, y_data, alpha = 1, label = 'Forecast', linestyle='--')
        # Shade the confidence interval
        plt.fill_between(x_data, low_CI, upper_CI, color = '#539caf', alpha = 0.4,
                         label = f'{confidence_level} confidence interval')

    # Plot actual data
    if actual is not None:
        actual = actual.sort_values(timestamp_col_name)
        plt.plot(actual[timestamp_col_name], actual[data_col_name], label = 'Actual', linestyle='--')

    # Display title, legend
    plt.title(f'{title}', fontsize=20)
    plt.legend(loc = 'upper center', prop={'size': 14})

# %% [markdown] id="Bez0o0Za8O1a"
# ### Prepare the weather data to be used during the model creation

# %% [markdown] id="qLcAc-rz9TAb"
# Let's create a BigQuery dataset which will contain several tables with data extracted from the WeatherNext dataset and a view to simplify queries.

# %% id="86b8mZGy-FE0"
%%bigquery --project {PROJECT_ID}

DECLARE latest_init_time TIMESTAMP;
DECLARE partition_metadata STRUCT<id STRING, year STRING, month STRING, day STRING>;

CREATE SCHEMA IF NOT EXISTS weathernext_derived OPTIONS (description = 'WeatherNext Forecasts - Derived', location = "US");

-- Find out the latest partition of the table.
SET partition_metadata = (
  SELECT
      STRUCT (partition_id AS id,
        SUBSTRING(partition_id, 0, 4) AS year,
        SUBSTRING(partition_id, 5, 2) AS month,
        SUBSTRING(partition_id, 7, 2) AS day)
      FROM weathernext_2_mean.INFORMATION_SCHEMA.PARTITIONS
      WHERE table_name = 'weathernext_2_0_0_mean' AND partition_id != '__NULL__'
      ORDER BY partition_id DESC
      LIMIT 1);

EXECUTE IMMEDIATE FORMAT("""
    SELECT MAX(init_time)
      FROM weathernext_2_mean.weathernext_2_0_0_mean
      WHERE init_time >= TIMESTAMP('%s-%s-%s 00:00:00')
  """, partition_metadata.year, partition_metadata.month, partition_metadata.day)
  INTO latest_init_time;

EXECUTE IMMEDIATE FORMAT("""
CREATE OR REPLACE VIEW `weathernext_derived.latest_forecast` AS
  SELECT * FROM `weathernext_2_mean.weathernext_2_0_0_mean` WHERE init_time = TIMESTAMP('%s')
""", STRING(latest_init_time));


# %% [markdown] id="SmqZm7qK-7oQ"
# We now have a dataset named `weathernext_derived`. This dataset has the `latest_forecast` view, which only returns the data from the latest forecast and ignores all historical data.
#
# Consider using the `latest_forecast` view to explore the contents of the dataset because it implements cost and performance effective partition pruning of the source table.
#
# You can re-run this cell as many times as you need to update the `latest_forecast` view (remember, the new forecast is automatically available every 6 hours).

# %% [markdown] id="ooNHuuXjBW-d"
# Here's the definition of the latest_forecast_view:

# %% id="wtQXaCTzBcvY"
!bq show --format=prettyjson '{PROJECT_ID}:weathernext_derived.latest_forecast'

# %% [markdown] id="V7IgYVVbGxlo"
# Now, we will extract the historic forecasts for the time period for which we plan to train some models. We are going to use two weather data points, temperature and precipitation, to do the forecasting. Note: we only use previous month's data to train the models. Using longer, or different, time periods might result in more accurate forecasting.

# %% id="WlP9NFkkHZe3"
%%bigquery --project {PROJECT_ID}

DECLARE historic_data_start_time DEFAULT TIMESTAMP_SUB(CURRENT_TIMESTAMP, INTERVAL 31 DAY);
DECLARE historic_data_end_time DEFAULT CURRENT_TIMESTAMP;

-- We use zip codes to identify the area we would like to forecast, but you can define
-- the area to cover in a number of different ways.
DECLARE zipcodes_to_cover DEFAULT ["10001", "10002"];
DECLARE geo_area_to_cover DEFAULT (
    WITH zip_areas AS (
      SELECT zip_code_geom as area
        FROM `bigquery-public-data.geo_us_boundaries.zip_codes`
        WHERE zip_code in UNNEST(zipcodes_to_cover))
    SELECT ST_UNION(ARRAY_AGG(area)) as combined_area FROM zip_areas);

-- Drop the existing table in case we need to re-create the forecast
DROP TABLE IF EXISTS weathernext_derived.historical_local_forecast;

CREATE TABLE weathernext_derived.historical_local_forecast AS (
WITH
all_forecast_points AS (
  SELECT
      geography,
      geography_polygon,
      forecast_point.time as forecast_time,
      -- The model sometimes produces very small negative precipitation numbers; here we normalize the data
      GREATEST(forecast_point.total_precipitation_6hr, 0.) as total_precipitation_6hr,
      forecast_point.`2m_temperature` as `2m_temperature`,
      -- Order the forecast points for same area in reverse chronological order of the forecast to pick the latest
      ROW_NUMBER() OVER (
        PARTITION BY ST_ASBINARY(geography),forecast_point.time
        ORDER BY init_time DESC) as row_number,
      ST_ASBINARY(geography) as location_id
  FROM weathernext_2_mean.weathernext_2_0_0_mean, UNNEST(forecast) as forecast_point
  WHERE
    -- Select enough data to cover the required time period
    init_time BETWEEN TIMESTAMP_SUB(historic_data_start_time, INTERVAL 12 HOUR) AND historic_data_end_time AND
    forecast_point.time BETWEEN TIMESTAMP_SUB(historic_data_start_time, INTERVAL 6 HOUR) AND historic_data_end_time AND
    -- Select all the forecasts that can be relevant
    ST_INTERSECTS(geo_area_to_cover, geography_polygon)
)
SELECT
    geography,
    geography_polygon,
    STRUCT(
        forecast_time,
        total_precipitation_6hr,
        `2m_temperature`,
        -- We also get the previous forecast for this location in order to make subsequent SQLs simpler
        LAG(`2m_temperature`) OVER(PARTITION BY location_id ORDER BY forecast_time) as prev_2m_temperature
    ) as forecast
  FROM all_forecast_points
  WHERE row_number = 1
);


# %% [markdown] id="kPRQCXcXJsZm"
# We now have the dataset of pretty accurate weather forecasts for a given area, spaced by 6 hours:

# %% id="HCGPs2ZbJ8lU"
%%bigquery historical_forecast --project {PROJECT_ID}

SELECT geography, forecast.forecast_time, forecast.total_precipitation_6hr, forecast.`2m_temperature`, forecast.`prev_2m_temperature`
  FROM weathernext_derived.historical_local_forecast
  WHERE forecast.prev_2m_temperature IS NOT NULL
  ORDER BY ST_ASBINARY(geography), forecast.forecast_time LIMIT 20


# %% id="5Db6tiWJLAQD"
display(historical_forecast)

# %% [markdown] id="TyrOjU-eDFU1"
# ### Move extracted weather data to the location of bus stop data

# %% [markdown] id="T0NKOfN6DWxM"
# If your bus stop data resides in the "US" BigQuery location then there is no need to do anything because the weather and the bus stop data are co-located and can be joined in the same query. Otherwise you will need to copy the extracted weather data. You can do that by using [cross-regional table copy](https://cloud.google.com/bigquery/docs/managing-tables#copy_tables_across_regions) capabilities of BigQuery.

# %% id="0VjEdNVGGJ9d"
%%bigquery --project {PROJECT_ID} --location {REGION}

CREATE SCHEMA IF NOT EXISTS multimodal;

DROP TABLE IF EXISTS multimodal.historical_local_forecast;

# %% id="y2XwaNPOFUqd"
! bq cp -f -n '{PROJECT_ID}:weathernext_derived.historical_local_forecast' '{PROJECT_ID}:multimodal.historical_local_forecast'

# %% [markdown] id="4ZeA3dCQPpVE"
# # Generate ridership data
#
# Let's assume that bus ridership depends on a number of factors - time of day, day of week, temperature and precipitation. We will generate a synthetic data set of bus ridership for several bus stops.

# %% [markdown] id="OeEJB9VBT7-m"
# ### Create ridership table

# %% id="9H2YWpgnUCRw"
%%bigquery

DROP TABLE IF EXISTS `multimodal.ridership`;

CREATE TABLE `multimodal.ridership`
  (bus_stop_id STRING, event_ts TIMESTAMP, temperature FLOAT64, total_precipitation_6hr FLOAT64, num_riders INT64)
  CLUSTER BY bus_stop_id;

# %% [markdown] id="aX6ZPXPwUGXE"
# ### Generate ridership events
#

# %% [markdown] id="Ozvfu5_V1807"
# We will generate ridership events based on a simple approach - generate an array of timestamps in the past, use an array with a couple of bus stops with some metadata (location, typical number of passengers, times of day and week these bus stops are typically busy, etc.). We will use real weather prediction data based on the time stop location and the time point to determine the likely temperature and precipitation. A temporary function will take all the metadata and the weather data and generate the number of riders.

# %% [markdown] id="Me3fliKA3dUc"
# Let's define a SQL function which approximates the temperature at a particular point in time. This function uses linear approximation between two forecasted temperatures 6 hours apart. This is not a perfect approximation formula for temperatures and can be replaced with more sophisticated one if needed.
#
# We will use this function for generation of the synthetic data and for actual forecasting:

# %% id="LboBZR0t3t3M"
%%bigquery --project {PROJECT_ID}

-- Approximate temperature. That assumes the previous temperature was forecast 6 hours ago.
CREATE OR REPLACE FUNCTION multimodal.temperature_approx(
  forecast STRUCT<
      time TIMESTAMP,
      total_precipitation_6h FLOAT64,
      `2m_temperature` FLOAT64,
      prev_2m_temperature FLOAT64 >, event_ts TIMESTAMP) AS (
    IF(forecast.prev_2m_temperature IS NULL,
      forecast.`2m_temperature`, -- There is no previous temperature; use the current one
      forecast.prev_2m_temperature +
        (forecast.`2m_temperature` - forecast.prev_2m_temperature) -- temperature span, potentially negative
        * (TIMESTAMP_DIFF(event_ts, TIMESTAMP_SUB(forecast.time, INTERVAL 6 HOUR), MINUTE)) -- number of minutes between the previous period and the time point
        / (6 * 60) -- number of minutes in 6 hours
    )
  );

# %% [markdown] id="lJdmnF4FBRXY"
# We also will create a table with a couple of fictitious bus stops - their ids, locations, and some meta data.

# %% id="VbnrddOPBicD"
%%bigquery --project {PROJECT_ID}

-- Two bus stops in New York, NY, USA
DECLARE bus_stop_location_1 DEFAULT ST_GEOGPOINT(-73.98886258282087, 40.745073789633736);
DECLARE bus_stop_location_2 DEFAULT ST_GEOGPOINT( -73.9899701866148, 40.714129256307956);

CREATE OR REPLACE TABLE multimodal.bus_stops AS (
SELECT bus_stop_id, location, base_number_of_riders, busy_in_morning, busy_in_evening, busy_on_weekend FROM UNNEST([
    STRUCT("bus-stop-1" as bus_stop_id, bus_stop_location_1 as location, 5 as base_number_of_riders, false AS busy_in_morning, true AS busy_in_evening, true AS busy_on_weekend),
    STRUCT("bus-stop-2" as bus_stop_id, bus_stop_location_2 as location, 10 as base_number_of_riders, true AS busy_in_morning, false AS busy_in_evening, false AS busy_on_weekend)])
);


# %% [markdown] id="l3_qIHUL4Pcr"
# Now, let's generate the ridership data:

# %% id="IouW45IIQvmm"
%%bigquery --project {PROJECT_ID}

DECLARE time_zone DEFAULT "America/New_York";

DECLARE end_ts DEFAULT CURRENT_TIMESTAMP();
-- One month worth of data
DECLARE start_ts DEFAULT TIMESTAMP_SUB(end_ts, INTERVAL 31 DAY);


-- This function generates the number of riders for a given time point
-- It uses several different factors and adds some variance.
CREATE TEMP FUNCTION generate_number_of_riders(
  base_number_of_riders INT64,
  busy_in_morning BOOL,
  busy_in_evening BOOL,
  busy_on_weekend BOOL,
  temperature FLOAT64,
  precipitation FLOAT64,
  event_ts TIMESTAMP)
AS (
  CAST(
    base_number_of_riders
    *
    -- Multiplier based on the temperature (in Kelvin)
    CASE
      -- Less than -3C/26F
      WHEN temperature < 270 THEN .7
      -- More than 32C/90F
      WHEN temperature > 305 THEN .4
      ELSE 1
    END
    *
    -- Multiplier based on precipitation.
    -- The higher the precipitation the fewer the riders.
    -- Precipitation is in meters; we multiply it by some weight.
    1/(1 + precipitation * 300)
    *
    -- Multiplier based on the day of week
    CASE
      -- 1 - Sunday
      WHEN EXTRACT(DAYOFWEEK FROM event_ts) BETWEEN 2 AND 6 THEN 2
      ELSE IF(busy_on_weekend, 3, 1)
    END
    *
    -- Multiplier based on the time of the day
    CASE
      -- No riders at night
      WHEN EXTRACT(HOUR FROM event_ts) BETWEEN 0 AND 6
        THEN 0
      -- Morning peak hours
      WHEN EXTRACT(HOUR FROM event_ts) BETWEEN 7 AND 9
        THEN IF(busy_in_morning, 1.5, 1.3)
      -- Evening peak hours
      WHEN EXTRACT(HOUR FROM event_ts) BETWEEN 15 AND 18
        THEN IF(busy_in_evening, 1.5, 1.3)
      -- Otherwise just the base number of riders
      ELSE 1
    END
    -- Add 20% variance
    * (.9 + (RAND()/5))
  AS INT64
  )
);


INSERT INTO multimodal.ridership (bus_stop_id, event_ts, temperature, total_precipitation_6hr, num_riders)
(
WITH
event_timestamps AS (
  SELECT TIMESTAMP(DATETIME(event_ts_in_utc, time_zone)) event_ts FROM
    UNNEST(GENERATE_TIMESTAMP_ARRAY(start_ts, end_ts, INTERVAL 5 MINUTE)) as event_ts_in_utc
),
bus_stops_and_event_timestamps AS (
  -- Cartesian join of the bus stops and time points
  SELECT bus_stops.*, event_ts FROM multimodal.bus_stops, event_timestamps
),
events_and_weather AS (
  SELECT
    bus_stop_id,
    event_ts,
    base_number_of_riders,
    busy_in_morning,
    busy_in_evening,
    busy_on_weekend,
    weather.forecast,
    multimodal.temperature_approx(weather.forecast, event_ts) as temperature,
    FROM bus_stops_and_event_timestamps events, multimodal.historical_local_forecast weather
      WHERE ST_COVERS(weather.geography_polygon, events.location) AND
        event_ts BETWEEN TIMESTAMP_SUB( weather.forecast.forecast_time, INTERVAL 6 HOUR) AND weather.forecast.forecast_time
)
  SELECT
    bus_stop_id,
    event_ts,
    temperature,
    forecast.total_precipitation_6hr as total_precipitation_6hr,
    generate_number_of_riders(
        base_number_of_riders,
        busy_in_morning,
        busy_in_evening,
        busy_on_weekend,
        temperature,
        forecast.total_precipitation_6hr,
        event_ts) num_riders
    FROM events_and_weather
);

# %% [markdown] id="3yMyeDdVUXHY"
# ### Visualize generated data

# %% [markdown] id="ue5rOAnkJ_IE"
# Let's take a look at the last 20 days of generated data. The first bus stop graph also shows the temperature and percipitation values. You should see some drop in ridership when preciptation increases or temperature is outside of the "comfortable" zone defined in the `generate_number_of_riders` function.

# %% id="9CtOQ1mBZR3M"
%%bigquery ridership_history

SELECT bus_stop_id, event_ts, num_riders, temperature, total_precipitation_6hr
  FROM `multimodal.ridership`
  WHERE event_ts > TIMESTAMP_SUB(CURRENT_TIMESTAMP, INTERVAL 20 DAY)

# %% id="GWVIBjf8Z2pK"
bus_stop_list = list(ridership_history.bus_stop_id.unique())
bus_stop_list.sort()

first_stop = True
for bus_stop_id in bus_stop_list:

    historical_data = ridership_history[ridership_history.bus_stop_id==bus_stop_id]
    plot_historical_and_forecast(historical_data = historical_data,
                                 timestamp_col_name = "event_ts",
                                 data_col_name = "num_riders",
                                 temperature_col_name="temperature" if first_stop else None,
                                 percipitation_col_name="total_precipitation_6hr" if first_stop else None,
                                 title = bus_stop_id)

    first_stop = False

# %% [markdown] id="hfMnFM06jIyJ"
# # Forecast bus ridership

# %% [markdown] id="ejbEK15cZa7I"
# Let's see how three built-in BigQuery models - TimesFM, ARIMA_PLUS and ARIMA_PLUS_XREG, can be used to do time-series forecasting.
#
# These models have a lot in common. We will use similar parameters to generate forecasts and will visualize the results.

# %% [markdown] id="5j3RFqYS5jMK"
# ## Univariate forecasting using the TimesFM model

# %% [markdown] id="cjbW-9r46UDv"
# [TimesFM](https://docs.cloud.google.com/bigquery/docs/timesfm-model) model is a pre-trained foundational model. There is no need to do custom model training, and for many use causes the model produces very accurate forecasting. As of May 2026, there are two model versions, "TimesFM 2.0" and "TimesFM 2.5". We will be using the latest model.
#

# %% [markdown] id="o2UM9OMmdTzd"
# ### Forecast ridership

# %% [markdown] id="boDoyVE9fV4y"
# Here's how to forecast the ridership for our bus stops:

# %% id="ECK9eNkTSYLY"
%%bigquery ridership_forecast --project {PROJECT_ID} --location {REGION}
DECLARE five_days_from_now DEFAULT TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 5 DAY);

EXECUTE IMMEDIATE FORMAT("""
SELECT bus_stop_id, forecast_timestamp, forecast_value, confidence_level, prediction_interval_lower_bound, prediction_interval_upper_bound
FROM
  AI.FORECAST(
    (
      SELECT bus_stop_id, num_riders, event_ts
FROM `multimodal.ridership` r),
    model => "TimesFM 2.5",
    forecast_end_timestamp => "%s",
    confidence_level => 0.8,
    timestamp_col => 'event_ts',
    data_col => 'num_riders',
    id_cols => ['bus_stop_id'])
ORDER BY bus_stop_id, forecast_timestamp
""", STRING(five_days_from_now));

# %% [markdown] id="67nvWracfCEj"
# Here's what we get as the result:

# %% id="0u7Oay8pfCEk"
display(ridership_forecast)

# %% [markdown] id="XjuY11TBfCEk"
# Let's visualize the forecast:

# %% id="QaFNeHEmfCEk"

bus_stop_list = list(ridership_history.bus_stop_id.unique())
bus_stop_list.sort()

for bus_stop_id in bus_stop_list:

    historical_data = ridership_history[ridership_history.bus_stop_id==bus_stop_id]
    forecast_data = ridership_forecast[ridership_forecast.bus_stop_id==bus_stop_id]
    plot_historical_and_forecast(historical_data = historical_data,
                                 timestamp_col_name = "event_ts",
                                 data_col_name = "num_riders",
                                 forecast_output = forecast_data,
                                 title = bus_stop_id)

# %% [markdown] id="ssQ8c1nqZvEc"
# ## Univariate forecasting using the ARIMA_PLUS model

# %% [markdown] id="myjZHzNVY02I"
# This model is trained purely on the time point input, hence it is a "univariate" model.
#
#

# %% [markdown] id="17SuJiPZ5XsH"
# ### Train the model

# %% [markdown] id="cOs-QLAe5bUP"
# The CREATE MODEL statement used to train the ARIMA_PLUS model has the usual time-series parameters - `time_series_data_col` to identify which data to forecast and `time_series_timestamp_col` to identify the column which contains the time point).
#
# It also has the `time_series_id_col` option. This option identifies the column which will identify a unique time-series within the trained data. In our case, after the training is done there will be two separate models - one for "stop1" and another for "stop2". There can be hundreds of thousands of time-series models created using a single CREATE MODEL statement.

# %% id="xiriX7sZY_5p"
%%bigquery --project {PROJECT_ID}

CREATE OR REPLACE MODEL `multimodal.ridership_arima_plus`
OPTIONS(
  model_type = 'ARIMA_PLUS',
  time_series_id_col = 'bus_stop_id',
  time_series_data_col = 'num_riders',
  time_series_timestamp_col = 'event_ts'
)
AS SELECT
  bus_stop_id,
  event_ts,
  num_riders
FROM `multimodal.ridership`;

# %% [markdown] id="ZuhrdnEV5rYn"
# ### Forecast ridership

# %% [markdown] id="geVFxNo-avF8"
# Let's forecast using this model. This is done by calling the table-valued-function (TVF) ML.FORECAST with a reference to the model trained in the prevous step. There is no additional data needed to forecast. The second parameter to the function affects how many data points since the last model training period is to produce ("horizon") and the level of confidence in the forecast values. For details, refer to the [ML.FORECAST documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-forecast).

# %% id="oGJFowYfa2V8"
%%bigquery arima_plus_forecast --project {PROJECT_ID}

SELECT
  *
FROM
  ML.FORECAST (
    model `multimodal.ridership_arima_plus`,
    STRUCT (1000 AS horizon, 0.8 AS confidence_level))
ORDER BY bus_stop_id, forecast_timestamp;

# %% [markdown] id="nb7jedUbc8wC"
# Here's the data returned by the forecast function:

# %% id="ktrbu9eBc1DZ"
display(arima_plus_forecast)

# %% [markdown] id="oJnF-fzF55Dq"
# #### Visualize the forecast

# %% [markdown] id="uypUNS9ybV_d"
# Looks like our forecast is pretty accurate based on the previous ridership pattern:

# %% id="6lllJZdRblqT"
bus_stop_list = list(ridership_history.bus_stop_id.unique())
bus_stop_list.sort()

for bus_stop_id in bus_stop_list:

    historical_data = ridership_history[ridership_history.bus_stop_id==bus_stop_id]
    forecast_data = arima_plus_forecast[arima_plus_forecast.bus_stop_id==bus_stop_id]
    plot_historical_and_forecast(historical_data = historical_data,
                                 timestamp_col_name = "event_ts",
                                 data_col_name = "num_riders",
                                 forecast_output = forecast_data,
                                 title = bus_stop_id)

# %% [markdown] id="6F7BaDwQaECx"
# ## Multivariate forecasting using the ARIMA_PLUS_XREG model

# %% [markdown] id="Vbk1qmXOmb9p"
# The ARIMA_PLUS_XREG model is called a "multivariate" model because in addition to the time points it also uses additional features, provided for each time point, to identify if they affect the time-series. In our case these features are the temperature and precipitation.

# %% [markdown] id="yzogKPO25C0H"
# ### Train the model

# %% [markdown] id="oqGe3Wzm5HV_"
# The same CREATE MODEL statement is used to train this model Many options, e.g,  `time_series_data_col`, `time_series_timestamp_col`,  `time_series_id_col` have the same meaning as for the ARIMA_PLUS model.
#
# The main difference - the ARIMA_PLUS_XREG model uses all columns besides those identified by the options above as the feature columns and uses linear regression to calculate covariate weights.
#
# For details on the additional options, explanation of the training process, and best practices when training and using the model please refer to BigQuery documentation on [the CREATE MODEL statement for ARIMA_PLUS_XREG models](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-create-multivariate-time-series).

# %% id="xM1y3GXljNwn"
%%bigquery

CREATE OR REPLACE MODEL `multimodal.ridership_arima_plus_xreg`
OPTIONS(
  model_type = 'ARIMA_PLUS_XREG',
  time_series_id_col = 'bus_stop_id',
  time_series_data_col = 'num_riders',
  time_series_timestamp_col = 'event_ts'
)
AS SELECT
  bus_stop_id,
  event_ts,
  num_riders,
  -- Two additional features that can affect the forecasting
  temperature,
  total_precipitation_6hr
FROM `multimodal.ridership`;

# %% [markdown] id="O4g_N5GukpKD"
# ### Forecast ridership

# %% [markdown] id="R279u7DGKVXs"
# Forecasting with the ARIMA_PLUS model was pretty simple. But in case of the XREG model we also need to provide the expected feature columns. We are going to need to get the weather forecast data ready.

# %% [markdown] id="IH05QFf3M1za"
# #### Get the latest weather forecast
#

# %% [markdown] id="GpA2HwFhNu4z"
# We have already prepared the historical data forecast. Now we are going to get the latest, most accurate, forecast extracted into a separate table.

# %% id="ag1RJVO9N8Id"
%%bigquery --project {PROJECT_ID}

-- We are going to use the same geo area as the one that we used for historical data generation

-- We use zip codes to identify the area we would like to forecast, but you can define
-- the area to cover in a number of different ways.
DECLARE zipcodes_to_cover DEFAULT ["10001", "10002"];
DECLARE geo_area_to_cover DEFAULT (
    WITH zip_areas AS (
      SELECT zip_code_geom as area
        FROM `bigquery-public-data.geo_us_boundaries.zip_codes`
        WHERE zip_code in UNNEST(zipcodes_to_cover))
    SELECT ST_UNION(ARRAY_AGG(area)) as combined_area FROM zip_areas);

DROP TABLE IF EXISTS weathernext_derived.latest_local_forecast;

CREATE TABLE weathernext_derived.latest_local_forecast AS (
  SELECT
      geography,
      geography_polygon,
      STRUCT(
        forecast_point.time as time,
        GREATEST(forecast_point.total_precipitation_6hr, 0.) as total_precipitation_6hr,
        forecast_point.`2m_temperature` as `2m_temperature`,
        LAG(`2m_temperature`) OVER(PARTITION BY ST_ASBINARY(geography) ORDER BY time) as prev_2m_temperature) as forecast
  -- "latest_forecast" is a view we generated in a previous step.
  -- A new forecast is created every 6 hours. To update the view to point to the latest forecast - rerun the block.
  FROM weathernext_derived.latest_forecast, UNNEST(latest_forecast.forecast) as forecast_point
  WHERE ST_INTERSECTS(geo_area_to_cover, latest_forecast.geography_polygon)
);


# %% [markdown] id="ZGN_FvGFyhnu"
# Let's see what's in that table:

# %% id="ROyUVU_dyqPx"
%%bigquery local_forecast --project {PROJECT_ID}

SELECT geography, forecast.time, forecast.total_precipitation_6hr, forecast.`2m_temperature`, forecast.`prev_2m_temperature`
  FROM weathernext_derived.latest_local_forecast
  WHERE forecast.prev_2m_temperature IS NOT NULL
  ORDER BY ST_ASBINARY(geography), forecast.time LIMIT 20

# %% id="qDPRYN53zn5L"
display(local_forecast)

# %% [markdown] id="0mFPcZuA0FnK"
# Let's move the latest forecast data to the location of the model:

# %% id="-8L08fxQK9Rk"
%%bigquery --project {PROJECT_ID}

DROP TABLE IF EXISTS multimodal.latest_local_forecast;

# %% id="yGb6uc-B06-b"
! bq cp -f -n '{PROJECT_ID}:weathernext_derived.latest_local_forecast' '{PROJECT_ID}:multimodal.latest_local_forecast'

# %% [markdown] id="RhQ_QkGxNjbg"
# #### Run the time-series forecast

# %% [markdown] id="VeOl0UzUHWve"
# If we were to use the ARIMA_PLUS model we could have just run the ML.FORECAST function to get time-series predictions. But the ARIMA_PLUS_XREG assumes that additional features will affect the forecast and you must provide the expected features to the ML.FORECAST function.
#
# We already have most of the parts to prepare the features. Let's first test the feature preparation SQL before running the model.
#
#

# %% id="ekoHAClRID0o"
%%bigquery expected_features --project {PROJECT_ID}

DECLARE time_zone DEFAULT "America/New_York";

-- Forecast from now...
DECLARE start_ts DEFAULT CURRENT_TIMESTAMP();
-- to 5 days forward
DECLARE end_ts DEFAULT TIMESTAMP_ADD(start_ts, INTERVAL 5 DAY);

WITH
event_timestamps AS (
  SELECT TIMESTAMP(DATETIME(event_ts_in_utc, time_zone)) event_ts FROM
    UNNEST(GENERATE_TIMESTAMP_ARRAY(start_ts, end_ts, INTERVAL 5 MINUTE)) as event_ts_in_utc
),
bus_stops_and_event_timestamps AS (
  -- Cartesian join of the bus stops and time points
  -- We only need the bus stop ids and locations, not all the meta data
  SELECT bus_stops.bus_stop_id, bus_stops.location, event_ts
    FROM multimodal.bus_stops, event_timestamps
),
events_and_weather AS (
  SELECT
    bus_stop_id,
    event_ts,
    weather.forecast,
    multimodal.temperature_approx(weather.forecast, event_ts) as temperature,
    -- we are getting the latest forecast data, not historical
    FROM bus_stops_and_event_timestamps events, multimodal.latest_local_forecast weather
      WHERE ST_COVERS(weather.geography_polygon, events.location) AND
        event_ts BETWEEN TIMESTAMP_SUB(weather.forecast.time, INTERVAL 6 HOUR) AND weather.forecast.time
)
SELECT
    bus_stop_id,
    event_ts,
    -- the two features used by the model
    temperature,
    forecast.total_precipitation_6hr as total_precipitation_6hr,
    FROM events_and_weather
    -- we are going to drop these clauses later, this is just to help with visualization
    ORDER by bus_stop_id, event_ts
    LIMIT 50;

# %% [markdown] id="Z4pdlEhjJDxr"
# Let's see what these features look like:

# %% id="_lsEtN5VJIYt"
display(expected_features)

# %% [markdown] id="qjNikfTFJvK-"
# OK, the features look correct. One nuance - you might see that the temperature values are unchanged for some earlier event timestamps. This is because our latest forecast table doesn't have temperature values for earlier forecasts and the temperature approximation function just takes the current value if there is no earlier one. We can find this data if needed by looking at the previous forecast, but that would result in more complex SQL statement.
#
# Let's run the forecast. We will use most of the feature preparation SQL in the forecasting function. Alternatively, we could have prepared the features and saved them in a table and used the whole table as the feature input to the forecast function.

# %% id="KcS2GPMqktw5"
%%bigquery ridership_forecast --location {REGION}

DECLARE time_zone DEFAULT "America/New_York";

-- Forecast from now...
DECLARE start_ts DEFAULT CURRENT_TIMESTAMP();
-- to 5 days forward
DECLARE end_ts DEFAULT TIMESTAMP_ADD(start_ts, INTERVAL 5 DAY);

SELECT
  *
FROM
  ML.FORECAST (
    model `multimodal.ridership_arima_plus_xreg`,
    STRUCT (1000 AS horizon, 0.8 AS confidence_level),
    (
WITH
event_timestamps AS (
  SELECT TIMESTAMP(DATETIME(event_ts_in_utc, time_zone)) event_ts FROM
    UNNEST(GENERATE_TIMESTAMP_ARRAY(start_ts, end_ts, INTERVAL 5 MINUTE)) as event_ts_in_utc
),
bus_stops_and_event_timestamps AS (
  -- Cartesian join of the bus stops and time points
  -- We only need the bus stop ids and locations, not all the meta data
  SELECT bus_stops.bus_stop_id, bus_stops.location, event_ts FROM multimodal.bus_stops, event_timestamps
),
events_and_weather AS (
  SELECT
    bus_stop_id,
    event_ts,
    weather.forecast,
    multimodal.temperature_approx(weather.forecast, event_ts) as temperature,
    -- we are getting the latest forecast data, not historical
    FROM bus_stops_and_event_timestamps events, multimodal.latest_local_forecast weather
      WHERE ST_COVERS(weather.geography_polygon, events.location) AND
        event_ts BETWEEN TIMESTAMP_SUB( weather.forecast.time, INTERVAL 6 HOUR) AND weather.forecast.time
)
SELECT
    bus_stop_id,
    event_ts,
    -- the two features used by the model
    temperature,
    forecast.total_precipitation_6hr as total_precipitation_6hr,
    FROM events_and_weather    )
  )
ORDER BY bus_stop_id, forecast_timestamp;

# %% [markdown] id="Qjh7K1_HlXwr"
# #### Visualize the forecast

# %% [markdown] id="1vPfTPSuVQnW"
# Here's what the ML.FORECAST function returns:

# %% id="Bix0T7drJF_E"
display(ridership_forecast)

# %% [markdown] id="tleV9kMlVjKU"
# Let's visualize the forecast:

# %% id="MI2t8RfHlbpT"

bus_stop_list = list(ridership_history.bus_stop_id.unique())
bus_stop_list.sort()

for bus_stop_id in bus_stop_list:

    historical_data = ridership_history[ridership_history.bus_stop_id==bus_stop_id]
    forecast_data = ridership_forecast[ridership_forecast.bus_stop_id==bus_stop_id]
    plot_historical_and_forecast(historical_data = historical_data,
                                 timestamp_col_name = "event_ts",
                                 data_col_name = "num_riders",
                                 forecast_output = forecast_data,
                                 title = bus_stop_id)

# %% [markdown] id="hM5NAO7mowoT"
# # Selecting the right model

# %% [markdown] id="GysbMt0ho5Ff"
# In the previous sections we have seen the mechanics of creating and using three time-series forecasting models. TimesFM model is the simplest to use (no need to train any models), but is the least customizable. The univariate ARIMA_PLUS model is simpler to create and is simpler to use for forecasting then the multivariate ARIMA_PLUS_XREG model. But the latter can give more accurate forecasting if there are external factors which have significant effect on the model outcome.
#
# In a real production implementation it would be important to capture the prediction results and compare with the actual outcomes. This would help to decide if it's worth building the multivariate model, fine tune other model parameters - training data period, additional features, effect of holidays and seasonality, etc.
#
# We also showed forecasting based on the immediate preceeding events (we used data from the previous 31 days). In many cases it might be more useful to use a different time range to base the forecast upon, e.g., the same period of the previous year. A word of caution: if you use this approach, consider that each timeseries model "completes" the data provided in the forecast with the data points which start from the last data point in the provided data. You would need to interpret the forecast with that in mind. The simplest thing to do would be to adjust to the resulting forecast's timestamps in the SQL query.

# %% [markdown] id="kMarPZ2DP4qf"
# ## Model evaluation
#
# Model evaluation should be part of the model selection process. You can't evaluate TimesFM model because it's a prebuilt model. But you evaluate the two variations of ARIMA_PLUS models using the ML.ARIMA_EVALUATE function.

# %% id="AqfIvpT5Ps4E"
%%bigquery arima_plus_model_evaluation --project {PROJECT_ID}

SELECT
  *
FROM
  ML.ARIMA_EVALUATE(MODEL multimodal.ridership_arima_plus, STRUCT(FALSE AS show_all_candidate_models))

# %% id="0FoUfb7WUlDO"
display_columns_as_rows(arima_plus_model_evaluation)

# %% [markdown] id="xcCjLpKHXB7a"
# You can see that there are multiple time series models under the over, one for each bus stop. For details on how to interpret the output of ML.ARIMA_EVALUATE function refer to the [BigQuery documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-arima-evaluate).

# %% [markdown] id="KNodZZ8IQCiD"
# ## Forecast explanation

# %% [markdown] id="C99xFgmVcwLP"
# To evaluate the forecast for TimesFM model, use the [AI.EVALUATE](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-evaluate) function:

# %% id="eRFz_LlsdBBJ"
%%bigquery timesfm_forecast_explanation --project {PROJECT_ID} --location {REGION}

DECLARE eval_cutoff DEFAULT TIMESTAMP_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY);

SELECT
  *
FROM
  AI.EVALUATE(
    (SELECT bus_stop_id, num_riders, event_ts FROM multimodal.ridership r WHERE event_ts <= eval_cutoff),
    (SELECT bus_stop_id, num_riders, event_ts FROM multimodal.ridership r WHERE event_ts > eval_cutoff),
    model => "TimesFM 2.5",
    horizon => 1000,
    timestamp_col => 'event_ts',
    data_col => 'num_riders',
    id_cols => ['bus_stop_id']
  )
ORDER BY bus_stop_id


# %% [markdown] id="pkfn-lS8mrBK"
# Here are the results of the evaluation:

# %% id="46pv6N-VnLmB"
display_columns_as_rows(timesfm_forecast_explanation)

# %% [markdown] id="K2jgJeqZQHJl"
# To evaluate the forecast for ARIMA_PLUS models, use the same parameters as use for ML.FORECAST function to call ML.EXPLAIN_FORECAST:

# %% id="vUCLXzghQd3A"
%%bigquery arima_plus_forecast_explanation --project {PROJECT_ID}

SELECT *
 FROM ML.EXPLAIN_FORECAST(
  MODEL multimodal.ridership_arima_plus,
  STRUCT(300 AS horizon, 0.8 AS confidence_level))
ORDER BY bus_stop_id, time_series_timestamp

# %% [markdown] id="ihstT3O6EM_G"
# The output of the function contains two types of records - the ones that were used for trainging and the actual forecast.
#
# Here are a couple of records of historical records:

# %% id="VEMbJ4Q4ROzK"
data_to_show = arima_plus_forecast_explanation[
    (arima_plus_forecast_explanation['bus_stop_id'] == 'bus-stop-1') &
    (arima_plus_forecast_explanation['time_series_type'] == 'history')]


display_columns_as_rows(data_to_show.head(2))

# %% [markdown] id="8QXl2XjWEsx9"
# And here are some for the forecast records:

# %% id="4jzn6HjYExXk"
data_to_show = arima_plus_forecast_explanation[
    (arima_plus_forecast_explanation['bus_stop_id'] == 'bus-stop-1') &
    (arima_plus_forecast_explanation['time_series_type'] == 'forecast')]


display_columns_as_rows(data_to_show.head(2))

# %% [markdown] id="tDBHRk4uThp6"
# For details on how to interpret the output of the function refer to the [BigQuery documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-explain-forecast).

# %% [markdown] id="6LW15mttL7QA"
# # Conclusion

# %% [markdown] id="CcuS8-5QWgPP"
# We showed how you can use three different time-series forecasting models available in BigQuery.
#
# We also showed how the WeatherNext Graph dataset can be used to get historical and future weather forecasts.
#
# There are multiple use cases for these time-series forecasts. For example, an AI agent can use the results of ridership forecast as an input to decision on how to perform a task like this: "In the next week schedule the repair of the bus stop #2 during the least impactful to passengers time".
