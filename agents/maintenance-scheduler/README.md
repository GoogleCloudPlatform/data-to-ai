# Bus Stop Maintenance Scheduling Agent

## Overview

This project implements an AI-powered bus stop maintenance scheduling agent (the agent).

## Agent Details

The agent's main task is to analyze open bus stop incidents, prioritize repairs, and dispatch
maintenance crews.
This is achieved through the following key features:

* **Rule-based Scheduling:** Bus stop selection can be prioritized using rules defined in natural
  language.
* **Flexible Operations:** The agent can operate in both interactive and autonomous modes.
* **Advanced AI Integration:** The agent combines BigQuery's time-series forecasting with the
  reasoning capabilities of the latest Gemini models.
* **Multi-Agent Collaboration:** Multiple agents are utilized to accomplish specific tasks.

### Agent Architecture

![Scheduling Agent Workflow](./agent-workflow.svg)

#### Tools

The agent has access to the following tools:

* **Get Unresolved Incidents:** Retrieves the list of incidents and bus stop data from BigQuery
* **Get Expected Number of Passengers:** Gets the time-series forecast of the bus ridership using
  BigQuery's TimesFM forecasting model
* **Get Current Time:** Returns the current time which will be used to schedule maintenance in the
  future
* **Is Time on Weekend:** Used by agent to schedule non-urgent maintenance during business hours.
* **Generate Email:** Uses a separate agent to generate well formatted email which will be sent to
  the maintenance crew
* **Schedule Maintenance:** Simulates the scheduling by updating the status of an incident with
  the "SCHEDULED" status and the notification details

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
   adk run maintenance_scheduler
   ```

2. Run agent with ADK Web UI:
   ```bash
   adk web
   ```
   Select the maintenance_scheduler from the dropdown

3. Interacting with the agent

The primary purpose of the agent is to respond to a request like "Check if there are any bus stops
which require maintenance."
A typical response will be:
> Here are the bus stops requiring maintenance and the description of each problem:
> * Bus stop #4 at 529 Old World quail Avenue, Anytown, NY, 10001: "The bus stop appears to be
    moderately dirty. There are leaves scattered on the sidewalk and along the curb. The bench shows
    signs of wear and tear, with some paint peeling. There is no visible graffiti or damage that
    would indicate vandalism. The bus stop has a bench and a sign. There are no immediate safety
    concerns. The steps leading to the house appear to be in disrepair."
> * Bus stop #17 at 6883 Platypus Street, Anytown, NY, 10001: "The bus stop shows signs of neglect.
    The bench is damaged, with significant wood missing from the seat and backrest. There is litter
    on the ground, including plastic bottles and a crumpled bag. The presence of litter and the
    damaged bench contribute to a low cleanliness score. There are no apparent safety hazards, such
    as broken glass or structural instability, so the safety level is high. The bus stop sign is
    intact and the trash can is present, but the overall condition of the stop is poor."
> * Bus stop #5 at 4999 list Avenue, Anytown, NY, 10001: "The bus stop appears to have some
    cleanliness issues. The sidewalk has some leaves and debris. The trash can is open and appears
    to have some trash inside. The bench has some wear and tear, but does not appear to be damaged.
    The curb has some discoloration and debris. There is no visible graffiti or signs of vandalism.
    The bus stop is located on a sidewalk next to a building. The overall cleanliness is not great,
    but there are no immediate safety concerns."
> * Bus stop #7 at 3643 Tasmanian devil Street, Anytown, NY, 10001: "The bus stop appears to be
    moderately dirty. There are leaves on the ground and some debris near the bench. The bench
    itself shows signs of wear and tear, but no immediate safety hazards are apparent. There is a
    trash can present, which suggests an effort to maintain cleanliness, but the presence of leaves
    and debris indicates that the area could benefit from cleaning. There is no visible graffiti or
    vandalism. The bus stop has a bench, a trash can, and a bus stop sign. The area appears safe."
> * Bus stop #16 at 8972 Porpoise Lane, Anytown, NY, 10001: "The bus stop appears to be in need of
    cleaning. The bench has a damaged backrest with peeling paint and is covered in leaves. The
    ground also has leaves scattered across it. There is no visible litter or graffiti. The bus stop
    sign is intact. There are no immediate safety concerns. The area is well-lit, and there are no
    obvious hazards."
    > Would you like me to schedule the maintenance for any of these bus stops?

You can ask the agent to proceed with the scheduling by simply replying "Yes". It will attempt to
prioritize the bus stops based on the [agent instructions](maintenance_scheduler/prompts.py).
Here's a typical response:

> I have the expected passenger numbers for the bus stops.<br>
> Based on this data and the current time (Wednesday, June 11, 2025, 4:07 PM), I will determine the
> best time to schedule maintenance for each stop, prioritizing by passenger traffic and aiming for
> regular working hours.<br>
> Let's start with Bus stop #5 at 4999 list Avenue, Anytown, NY, 10001. It has the highest average
> passenger traffic. The issue is: "The bus stop appears to have some cleanliness issues. The
> sidewalk
> has some leaves and debris. The trash can is open and appears to have some trash inside. The bench
> has some wear and tear, but does not appear to be damaged. The curb has some discoloration and
> debris. There is no visible graffiti or signs of vandalism. The bus stop is located on a sidewalk
> next to a building. The overall cleanliness is not great, but there are no immediate safety
> concerns."<br>
> This seems like a general cleaning job. I'll look for a time with low passenger traffic during
> working hours.<br>
> Considering the passenger forecast, a good time to schedule this would be Thursday, June 12, 2025,
> at 9:00 AM EST when passenger numbers are very low. This will take approximately 3 hours.<br>
> Would you like me to schedule the maintenance for bus stop #5 at this time?

Again, you can reply with "Yes". The agent will respond with something along the lines of:

> Great. I've scheduled the maintenance for bus stop #5 at 4999 list Avenue for Thursday, June 12,
> 2025, at 9:00 AM EST.<br>
> Now let's move on to the next bus stop.<br>
> Bus stop #17 at 6883 Platypus Street, Anytown, NY, 10001 also has high passenger traffic.<br>
> ... rest of the agent response ...

This process will continue until there are no more bus stops that require maintenance.

The agent can respond to other prompts. You can experiment using these examples:

* Describe yourself
* What is the URL of the image of the bus stop #7?
* Schedule the maintenance of bus stop 5 at a different time
* Show the email notification generated for the bus stop 5

**Important:** The agent's instructions for this agent have not been fine-tuned. We used simple
plain
natural language to describe the work that the agent needs to perform. In our testing the reasoning
that the agent did was very good with occasional scheduling suggestions that
required correction. For production deployments additional tuning is recommended. Refer to
the [Prompting Strategies](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/prompt-design-strategies)
documentation for specific recommendations.

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

You can find further configuration parameters
in [maintenance_scheduler/config.py](maintenance_scheduler/config.py). This includes parameters such
as agent name, app name and LLM model used by the agent. Most of the parameters can be configured by
overriding the default values in the `.env` file.

[//]: # (TODO: explain how thoughts can be used and autonomous vs interactive configs)

## Deployment to Google Agent Engine

In order to inherit all dependencies of your agent you can build the wheel file of the agent and run
the deployment.

1. **Build Customer Service Agent WHL file**

    ```bash
    poetry build --format=wheel --output=deployment
    ```

2. **Deploy the agent to Agent Engine**
   It is important to run deploy.py from withing deployment folder so paths are correct

    ```bash
    cd deployment
    python deploy.py
    ```

3. **Capture the deployed agent's resource name
   If the deployment successful, the script will print a line similar to this:
    ```shell
    INFO:root:Agent deployed successfully under resource name: projects/<project_number>/locations/us-central1/reasoningEngines/<numeric_id>
    ```
   Capture the resource name and update `GOOGLE_AGENT_RESOURCE_NAME` variable in the `.env` file.

3. **Grant the service account running the engine required permissions**
   When the agent is deployed to the Agent Engine it is run in the context of a
   particular service account. Please
   see [Vertex AI Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/set-up#service-agent)
   for details.

   The agent uses tools which need access to the BigQuery data and need to be able to run queries.
   The Terraform script [agent-engine.tf](../../infrastructure/terraform/agent-engine.tf) added all
   the necessary permissions.
   If you need to add additional permissions you can use the script below as an example to manually
   add them:

    ```bash
    gcloud beta services identity create --service=aiplatform.googleapis.com --project=${GOOGLE_CLOUD_PROJECT}
    GOOGLE_CLOUD_PROJECT_NUMBER=$(gcloud projects describe ${GOOGLE_CLOUD_PROJECT} --format="value(projectNumber)")
    AGENT_ENGINE_SA="service-${GOOGLE_CLOUD_PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
    bq add-iam-policy-binding --member="serviceAccount:${AGENT_ENGINE_SA}" --role='roles/bigquery.dataEditor' "${GOOGLE_CLOUD_PROJECT}:bus_sto
    bq add-iam-policy-binding --member="serviceAccount:${AGENT_ENGINE_SA}" --role='roles/bigquery.dataViewer' "${GOOGLE_CLOUD_PROJECT}:bus_sto
    bq add-iam-policy-binding --member="serviceAccount:${AGENT_ENGINE_SA}" --role='roles/bigquery.dataViewer' "${GOOGLE_CLOUD_PROJECT}:bus_sto
    p_image_processing.bus_stops"
    ```

### Testing the Agent Engine deployment

1. **Run the test script**
   At the agents/maintenance-scheduler directory run:
    ```bash
    python test_deployed_agent.py
    ```

   You should see output similar to this:
    ```text
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

## Deployment to Agentspace

Once the Agent Engine deployment is successful, the agent can be enabled on an Agentspace app.
Agentspace will be the UI of the agent.

### Create a new Agentspace instance

Once the instance is created, capture the so-called "app id" of that instance and
update the `AGENTSPACE_APP_ID` variable in the `.env` file.

### Deploy the agent into the Agentspace

Run the following script:

```shell
./register-with-agentspace.sh
```

### Use the agent

Navigate to the Agentspace app and click on the Bus Stop Maintenance Scheduler link
under the Agents menu.

Use the agent the way you used it when testing the agent locally.

## Using MCP Toolbox for Databases

By default, the agent uses tools which interact with BigQuery using the BigQuery Python client
library. Calls to BigQuery APIs are made directly from the agent. In many cases it might be
desirable to move this functionality to a dedicated
server. [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/getting-started/introduction/)
is one such option.

### Get the latest version of the Toolbox

Follow the instructions
on [this page](https://github.com/googleapis/genai-toolbox?tab=readme-ov-file#getting-started)

### Start the server

After the Terraform scripts successfully completed, the root directory of this repository will
contain a small shell script, ".cloud-env.sh". This script will define environment variables which
will be used to configure the toolbox.

From the `agents/mcp-toolbox` directory run:

```shell
source ../../.cloud-env.sh 

<installation path>/toolbox --tools-file=maintenance-scheduler-tools.yaml  --log-level=DEBUG
```

### Verify that the toolbox is running and is responds to the tool discovery calls

```shell
curl -H "Accept: application/json" http://127.0.0.1:5000/api/toolset | jq .
```

You should expect to see the response like this:

```json
{
  "serverVersion": "0.9.0+binary.darwin.arm64.2b69700c5e40ad37eafd94f378a2e1174879402b",
  "tools": {
    "get-expected-number-of-passengers": {
      "description": "Provides expected number of passengers for a particular bus stop at some point in the future.\n",
      "parameters": [
        {
          "name": "bus_stop_ids",
          "type": "array",
          "required": true,
          "description": "Bus stop ids",
          "authSources": [],
          "items": {
            "name": "bus_stop_id",
            "type": "string",
            "required": true,
            "description": "Bus stop id",
            "authSources": []
          }
        },
        {
          "name": "time_zone",
          "type": "string",
          "required": true,
          "description": "Time zone of where the bus stops are located",
          "authSources": []
        }
      ],
      "authRequired": []
    },
    "get-unresolved-incidents": {
      "description": "Provides the list of unresolved bus stop incidents which require maintenance\n",
      "parameters": [],
      "authRequired": []
    },
    "schedule-maintenance": {
      "description": "Provides expected number of passengers for a particular bus stop at some point in the future.\n",
      "parameters": [
        {
          "name": "bus_stop_id",
          "type": "string",
          "required": true,
          "description": "Bus stop id",
          "authSources": []
        },
        {
          "name": "maintenance_start",
          "type": "string",
          "required": true,
          "description": "Maintenance start time",
          "authSources": []
        },
        {
          "name": "reason",
          "type": "string",
          "required": true,
          "description": "Reason for maintenance",
          "authSources": []
        },
        {
          "name": "notification_subject",
          "type": "string",
          "required": true,
          "description": "Subject of the notification email",
          "authSources": []
        },
        {
          "name": "notification_content",
          "type": "string",
          "required": true,
          "description": "Contents of the notification email",
          "authSources": []
        }
      ],
      "authRequired": []
    }
  }
}
```

The command above uses the toolset's custom API, which is used by the Python's ToolboxSyncClient. If
this toolset is going to be accessed using a client which utilizes the MCP protocol, a different API
will be used for discovery:

```shell
 curl -d '{"jsonrpc":"2.0","method":"tools/list","id":"tool_discovery_request_1"}' -N \
 -H "Accept: application/json" -H "Content-Type: application/json" http://127.0.0.1:5000/mcp | jq .
```

The server will respond with the same list of tools, but using the MCP message format.

You can
also [use MCP Inspector](https://googleapis.github.io/genai-toolbox/getting-started/mcp_quickstart/#step-3-connect-to-mcp-inspector)
for a more comprehensive analysis of the toolbox functionality.

### Change the agent configuration

Edit the `.env` file in the "agents/maintenance-scheduler/maintenance_scheduler" folder to have
these lines:

```shell
use_mcp_toolbox=True
mcp_toolbox_uri=http://127.0.0.1:5000
```

### Run the agent

Restart the ADK if it's already running and execute the first prompt. When check at the toolbox's
terminal window you will see several GET calls to "/api/tool/<tool-name>" - they are part of the
toolbox client initialization process. Once the agent starts using tools, there will be
corresponding POST calls to the toolbox.

Run the scheduling process for a bus stop until the end to verify that all the tools behave as if
they were in-agent tools.

### Using the toolbox in production

You can deploy the toolbox to a number of cloud services,
including [Cloud Run](https://googleapis.github.io/genai-toolbox/how-to/deploy_toolbox/)
and [GKE](https://googleapis.github.io/genai-toolbox/how-to/deploy_gke/). The agent code would need
to be modified slightly to enable the right authentication. See [this documentation section] for
details. 

## Troubleshooting the agent

### The agent doesn't prioritize maintenance of the right bus stop

There could be a number of reasons for that. But remember that LLMs are not deterministic. It's
possible that the agent is going to take a different "path" than a human when trying judge multiple
criteria. If you see a systematic deviation from the desired output try:

* Make sure that the description of the bus stop images is aligned with the agent goals. E.g., that
  the description describes possible safety concerns and talks about the bus stop cleanliness rather
  than, let's say, the location of the bus stop, weather, etc.
* Verify that the "get the number of passengers" tool correctly returns predictions. See next
  section.
* Enable the `show_thought` configuration parameter. It might help find a logical flaw in the
  instructions.
* Capture the output of the "get the incidents" and "get the number of passengers" function, create
  mock data in the tools module and try to run the agent multiple times under the same scenario. See
  if it was a one-time hallucination or a consistently erroneous suggestion. If it's the latter you
  will need to redesign your prompt.

In the next version of the agent we will add the evaluation process which will show how some manual
steps above can be automated and how a production quality agent can be created.

### The "get the number of passengers" tool doesn't return any data

That tool uses a BigQuery time-series ML function that relies on the data in the bus_ridership
table. If the data in that table is stale, the ML function will not be able to predict the data in
the future. Please run the following BigQuery statements to generate new synthetic ridership data:

```sql
TRUNCATE TABLE bus_stop_image_processing.bus_ridership;
CALL bus_stop_image_processing.generate_synthetic_ridership();
```



