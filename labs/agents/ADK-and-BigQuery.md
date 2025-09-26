# Instructions on running the ADK and BigQuery lab

## Goals

This lab will show different ways to access data in BigQuery from custom agents built using the open
source Agent Development Kit (ADK).

You will learn how to create custom tools to access BigQuery and how to use an MCP server which
implements a number of pre-built BigQuery tools.

*Note*: ADK is a generic agent framework which allows creating sophisticated agents using
workflows (sequential, parallel or custom sequencing) and parent/child/sibling agent
compositions, offers session and state management and has a number of other features. The best
practices and design patterns of creating complex agents is outside the scope of this lab.

## Prerequisites

The lab assumes you ran all the code cells the
notebook [genai_in_bigquery.ipynb](./../genai_in_bigquery.ipynb).
The following BigQuery objects should be created:

* `multimodal` BigQuery dataset with three tables:
    * `objects` - object table pointing to a small set of images
    * `image_reports` - outcome of the LLM processing of these images
    * `image_reports_vector_db` - text embeddings of the descriptions of the images

You should have sufficient permissions to enable additional APIs and should have privileges to read
the tables listed above.

## Running the agent

If you have access to a computer with Python 3.11 and above installed you can run this lab on that
computer. The rest of the instructions assume that the agent will be run
in [Cloud Shell](https://cloud.google.com/shell/docs).

### Start the Cloud Shell

Click ![Cloud Shell icon](https://cloud.google.com/static/shell/docs/images/activate-cloud-shell-button.svg)
Activate Cloud Shell at the top of the Google Cloud console.

### Clone the public GitHub repository with the agent code

```shell
git clone https://github.com/GoogleCloudPlatform/data-to-ai.git

cd data-to-ai/labs/agents/
```

### Download and Run an MCP server

We are going to
use [MCP Toolbox for Database](https://googleapis.github.io/genai-toolbox/getting-started/introduction/).

Switch to the directory which contains the server configuration:

```shell
cd data-to-ai/labs/agents/adk_and_bigquery/mcp
```

Download the server:

```shell
export VERSION=0.16.0
curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
chmod +x toolbox

./toolbox --version
```

You should see output like this:

```
toolbox version 0.16.0+binary.linux.amd64.964a82e
```

Set the environment variables which are referenced by the configuration file, mcp.yaml:

```shell
export BIGQUERY_DATA_LOCATION=us-central1

CURRENT_PROJECT=$(gcloud config get-value core/project)
export BIGQUERY_DATA_PROJECT_ID=${CURRENT_PROJECT}
export BIGQUERY_RUN_PROJECT_ID=${CURRENT_PROJECT}
```

The above setup assumes that your current shell's default project is the one where the BigQuery
dataset resides and where the queries will be run. Adjust these variables if this is not the case.

Start the MCP server:

```shell
./toolbox --tools-file=mcp.yaml --ui
```

You should see the last line of the output stating that
`Toolbox UI is up and running at: http://127.0.0.1:5000/ui`.

*Optional*: verify that the MCP server is running by clicking on the Web Preview
icon (![Web Preview](https://cloud.google.com/static/shell/docs/images/web_preview.svg)) on the
upper right side of the Cloud Shell terminal and change the port to 5000. You will see a "Hello
World" message. Add "/ui" to the URL and reload the page. You should the server's welcome page:

![MCP Server Welcome Page](docs/MCP%20Toolbox%20Welcome%20Page.png)

You can explore the Tools tab and try out MCP Tools.

We will let the MCP server run in this Cloud Shell tab.

To run the agent itself, open another tab by clicking on the + icon on at the top of the terminal
window. You will see a new terminal window. First, let's natigate to the directory with the agent
code.

```shell
cd ~/data-to-ai/labs/agents/
```

### Set up the Python environment

We used ADK's Python SDK to create the agent.

```shell
python -m venv .venv
source .venv/bin/activate

pip install --upgrade google-adk
```

### Running the agent locally

We are now ready to run and test our agent locally. There are several ways to do it - using scripts
or using ADK CLI (`adk run`), but the most efficient way to see how ADK agents work is to run them using integrated UI:

```shell
adk web
```
You should see `Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`.

To access the ADK Web UI select the Web Preview icon again and change the port to 8000. You should see a page similar to this:
![ADK UI](docs/ADK%20UI.png).



