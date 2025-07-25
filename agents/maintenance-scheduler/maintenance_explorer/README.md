# Bus Stop Maintenance Exploring Agent

## Overview

This project implements a  AI-powered bus stop maintenance exploring agent that will allow you query and obtain information about Bust Stops, incidents, images, etc.

NOTE : this agent have only read capabilities on the Lakehouse tables in order to easy explore an analyse the bus stops information, pictures and incidents. In order execute actions and schedule mantaince crew please usee the Maintenance_Scheduler agent agent. 

## Agent Details

The agent's main task is to help you to interact with you Lakehouse architecture in order to understand the  analyze open bus stop incidents, prioritize repairs, display picture of bus stops ,etc

This is achieved through the following key features:

* **Flexible Data Exploring Operations:** Via Conversational Analtyics API, the agent will be able to query the AI Lake house.

* **Flexible Data Exploring Operations:**
### Agent Architecture

![Scheduling Agent Workflow](./agent-explre-workflow.svg)

#### Tools

The agent has access to the following tools:

* **Lake house:** Using Big Query Conversational Analytics API is able to answer questions about bus stops
* **Display Image from bucket  :** Will be able to display an image of an Bus Stop.

## Setup and Installations

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Google ADK SDK (installed via Poetry)
- Google Cloud Project (for Vertex AI Gemini integration)

### Installation

1. **Prerequisites:**
   Run the Terraform scripts described in
   the [Getting Started with the Terraform](https://github.com/GoogleCloudPlatform/data-to-ai/tree/maintenance-scheduler-agent?tab=readme-ov-file#getting-started-with-the-terraform)
   section of the top level README file.

Make sure to run the scripts that process the test data, e.g. run at least one `upload-batch.sh`
invocation and make sure that both `process_images` and `update_incidents` stored procedures
have been run. At the end of this process you will have several records in the `incidents` table
with the status "OPEN".

Additionally, execute the `generate_synthetic_ridership` stored procedure. The data generated in
this step will be used to forecast the number of riders.

This is the starting point for the agent to start scheduling maintenance.

1. Switch to the agent's directory

   ```bash
   cd agents/maintenance-scheduler
   ```

   For the rest of this tutorial **ensure you remain in the `agents/maintenance-scheduler` directory
   **.

2. Install dependencies using Poetry:

- if you have not installed poetry before then run `pip3 install poetry` first. Then you can create
  your virtual environment and install all dependencies using:

  ```bash
  poetry install
  ```

  To activate the virtual environment run:

  ```bash
  poetry env activate
  ```

3. Set up environment variables that will be used by the local version of ADK
    - Set the `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION`
      environment variables. You can set them in your `.env` file (modify and rename .env_sample
      file to .env) or directly in your shell.

   ```bash
   export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID_HERE
   export GOOGLE_GENAI_USE_VERTEXAI=1
   export GOOGLE_CLOUD_LOCATION=us-central1
   ```

## Running the Agent

You can run the agent using the ADK command in your terminal.

1. Run agent in CLI:

   ```bash
   adk run maintenance_explorer
   ```

2. Run agent with ADK Web UI:
   ```bash
   adk web
   ```
   Select the maintenance_explorer from the dropdown

3. Interacting with the agent

The primary purpose of the agent is to respond to a request like:

 - "Check if there are any bus stops which require maintenance."
 - "Display image of bus stop 5"
 - "Can you please make a summary of the bus Maintenance status?"
 - "Show me list of that require maintenance with their  bus stops with their address, bus stop number, description of the incident "

NOTE: For debuging porpuse we instruected the Agent to return the SQL quere that was made to the Lakehouse.
**Important:** The agent's instructions for this agent have not been fine-tuned. We used simple plain
natural language to describe the work that the agent needs to perform. In our testing the reasoning
that the agent did was very good with occasional scheduling suggestions that
required correction. For production deployments additional tuning is recommended. Refer to
the [Prompting Strategies](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/prompt-design-strategies)
documentation for specific recommendations.



## Configuration

You can find further configuration parameters
in [maintenance_scheduler/config.py](maintenance_scheduler/config.py). This includes parameters such
as agent name, app name and LLM model used by the agent. Most of the parameters can be configured by
overriding the default values in the `.env` file.

