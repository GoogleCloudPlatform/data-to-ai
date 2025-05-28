# Bus Stop Maintenance Scheduling Agent

## Overview

This project implements an AI-powered bus stop maintenance scheduling agent. 

## Agent Details

The key features of the scheduling agent include integration with BigQuery and advanced reasoning
capabilities prioritizing scheduling of one bus stop over the other.

### Agent Architecture

![Scheduling Agent Workflow](./agent-workflow.svg)


### Key Features

[//]: # (TODO: add descriptions)

#### Tools

The agent has access to the following tools:

[//]: # (TODO: add tool descriptions)

## Setup and Installations

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Google ADK SDK (installed via Poetry)
- Google Cloud Project (for Vertex AI Gemini integration)

### Installation
1.  **Prerequisites:**

    For the Agent Engine deployment steps, you will need
    a Google Cloud Project. Once you have created your project,
    [install the Google Cloud SDK](https://cloud.google.com/sdk/docs/install).
    Then run the following command to authenticate with your project:
    ```bash
    gcloud auth login
    ```
    You also need to enable certain APIs. Run the following command to enable
    the required APIs:
    ```bash
    gcloud services enable aiplatform.googleapis.com
    ```

1.  Clone the repository:

    ```bash
    git clone https://github.com/GoogleCloudPlatform/data-to-ai.git
    cd agents/maintenance-scheduler
    ```

    For the rest of this tutorial **ensure you remain in the `agents/maintenance-scheduler` directory**.

2.  Install dependencies using Poetry:

- if you have not installed poetry before then run `pip3 install poetry` first. Then you can create your virtual environment and install all dependencies using:

  ```bash
  poetry install
  ```

  To activate the virtual environment run:

  ```bash
  poetry env activate
  ```

3.  Set up Google Cloud credentials:

    - Ensure you have a Google Cloud project.
    - Make sure you have the Vertex AI API enabled in your project.
    - Set the `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT`, and `GOOGLE_CLOUD_LOCATION` environment variables. You can set them in your `.env` file (modify and rename .env_sample file to .env) or directly in your shell. Alternatively you can edit [customer_service/config.py](maintenance_scheduler/config.py)

    ```bash
    export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID_HERE
    export GOOGLE_GENAI_USE_VERTEXAI=1
    export GOOGLE_CLOUD_LOCATION=us-central1
    ```

## Running the Agent

You can run the agent using the ADK commant in your terminal.
from the root project directory:

1.  Run agent in CLI:

    ```bash
    adk run maintenance_scheduler
    ```

2.  Run agent with ADK Web UI:
    ```bash
    adk web
    ```
    Select the maintenance_scheduler from the dropdown

[//]: # (### Example Interaction - TODO)

[//]: # ()
[//]: # (## Evaluating the Agent)

[//]: # ()
[//]: # (Evaluation tests assess the overall performance and capabilities of the agent in a holistic manner.)

[//]: # ()
[//]: # (**Steps:**)

[//]: # ()
[//]: # (1.  **Run Evaluation Tests:**)

[//]: # (    [//]: # &#40;TODO: implement&#41;)

[//]: # (    ```bash)

[//]: # (    pytest eval)

[//]: # (    ```)

[//]: # ()
[//]: # (    - This command executes all test files within the `eval` directory.)

[//]: # ()
[//]: # (## Unit Tests)

[//]: # ()
[//]: # (Unit tests focus on testing individual units or components of the code in isolation.)

[//]: # ()
[//]: # (**Steps:**)

[//]: # ()
[//]: # (1.  **Run Unit Tests:**)

[//]: # ()
[//]: # ([//]: # &#40;TODO: implement&#41;)
[//]: # (    ```bash)

[//]: # (    pytest tests/unit)

[//]: # (    ```)

[//]: # ()
[//]: # (    - This command executes all test files within the `tests/unit` directory.)

## Configuration

You can find further configuration parameters in [maintenance_scheduler/config.py](maintenance_scheduler/config.py). This includes parameters such as agent name, app name and LLM model used by the agent.

## Deployment on Google Agent Engine

In order to inherit all dependencies of your agent you can build the wheel file of the agent and run the deployment.

1. **Build Customer Service Agent WHL file**

    ```bash
    poetry build --format=wheel --output=deployment
    ```

2. **Deploy the agent to agents engine**
    It is important to run deploy.py from withing deployment folder so paths are correct

    ```bash
    cd deployment
    python deploy.py
    ```
3. **Grant the service account running the engine required permissions**
    When the agent is deployed to the Agent Engine it is run in the context of a 
    particular service account. Please see [Vertex AI Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/set-up#service-agent) for details.
    
    The agent uses tools which need access to the BigQuery data and need to be able to run queries.
    The Terraform script [agent-engine.tf](../../infrastructure/terraform/agent-engine.tf) added all the necessary permissions.
    If you need to add additional permissions you can use the script below as an example to manually add them.
```bash
gcloud beta services identity create --service=aiplatform.googleapis.com --project=${GOOGLE_CLOUD_PROJECT}
GOOGLE_CLOUD_PROJECT_NUMBER=$(gcloud projects describe ${GOOGLE_CLOUD_PROJECT} --format="value(projectNumber)")
AGENT_ENGINE_SA="service-${GOOGLE_CLOUD_PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
bq add-iam-policy-binding --member="serviceAccount:${AGENT_ENGINE_SA}" --role='roles/bigquery.dataEditor' "${GOOGLE_CLOUD_PROJECT}:bus_sto
bq add-iam-policy-binding --member="serviceAccount:${AGENT_ENGINE_SA}" --role='roles/bigquery.dataViewer' "${GOOGLE_CLOUD_PROJECT}:bus_sto
bq add-iam-policy-binding --member="serviceAccount:${AGENT_ENGINE_SA}" --role='roles/bigquery.dataViewer' "${GOOGLE_CLOUD_PROJECT}:bus_sto
p_image_processing.bus_stops"
```

### Testing deployment

1. **Update .env file with the agent id**
    When the deployment is successful, the last line of the output will be: 
    "Agent deployed successfully under resource name: projects/XXX/locations/us-central1/reasoningEngines/YYY"
Copy the resource name and update the environment variable `GOOGLE_AGENT_RESOURCE_ID` in `.env` file.

   2. **Run the test script**
       At the agents/maintenance-scheduler directory run:
       ```bash
       python test_deployed_agent.py
       ```
    
       You should see output similar to this:
       ```json
       {'content': {'parts': [{'thought': True,
                           'text': "Alright, here's what's running through my "
                                   "mind: The user's asking about bus stop "
                                   'maintenance. Before I give them an answer, I '
                                   'need to check the system for any outstanding '
                                   "issues. My first step is clear: I'll leverage "
                                   "the `get_unresolved_incidents` tool. That'll "
                                   'pull up a list of any open bus stop '
                                   'maintenance requests.\n'
                                   '\n'
                                   "Once I get the data back, I'll interpret the "
                                   'results. If the list is empty – fantastic! I '
                                   'can tell the user straight away that '
                                   "everything's in good shape, no immediate "
                                   'action needed. But if there *are* open '
                                   "incidents, I'll need to be more specific. "
                                   "I'll let the user know maintenance is "
                                   'required and perhaps even provide a quick '
                                   "summary of the types of issues we're dealing "
                                   'with.\n'
                        ...
   ```

