# Copyright 2025 Google LLC
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

"""Database Agent: get data from database (BigQuery) using Conversation Analytics API."""

import os

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from .tools import tools
from google.cloud import geminidataanalytics
from google.adk.planners import BuiltInPlanner
from google.genai.types import ThinkingConfig
from .tools.tools import ask_lakehouse,get_image_from_bucket,analytics_chart_tool,get_external_url_image
from .config import Config
from .prompts import GLOBAL_INSTRUCTION, INSTRUCTION
from google.adk.tools import FunctionTool
from google.genai import types
import io
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from toolbox_core import ToolboxSyncClient

import logging
logger = logging.getLogger(__name__)

configs = Config()

def add_tables(table_names:[],bq_dataset_id:str,billing_project:str) -> None: 
    bigquery_table_references=[]
    for table_name in table_names:
            bigquery_table_reference = geminidataanalytics.BigQueryTableReference()  # Assuming geminidataanalytics is your library
            bigquery_table_reference.project_id = billing_project
            bigquery_table_reference.dataset_id = bq_dataset_id
            bigquery_table_reference.table_id = table_name  # Use the current table name from the loop
            bigquery_table_references.append(bigquery_table_reference)  # Store the created object if needed
    return bigquery_table_references


def create_ca_agent(parent_agent_name:str,agent_id:str,agent_name:str, billing_project:str)-> None:
    # Make the request to see if the agents and conversation were created if not create them
    try:
        data_agent_client = geminidataanalytics.DataAgentServiceClient()
        request_list = geminidataanalytics.ListDataAgentsRequest(
            parent=parent_agent_name,)       
        page_result = data_agent_client.list_data_agents(request=request_list)
        exist_agent = False
        for response in page_result:
            if (str(response.name) == agent_name):
                logger.info(f"Data Agent  {agent_name} already exists")
                exist_agent = True
                break
        
        if not exist_agent:
            logger.info("Creating a new agent  %s",agent_name )
            data_agent_client = geminidataanalytics.DataAgentServiceClient()
            bigquery_table_references=[]

            bq_dataset_id = configs.BQ_DATASET
            table_names = ["bus_stops","image_reports","incidents","report_watermark","bus_ridership"]
            bigquery_table_references =  add_tables(table_names,bq_dataset_id,billing_project)

            datasource_references = geminidataanalytics.DatasourceReferences()
            datasource_references.bq.table_references = bigquery_table_references
        
            # Set up context for stateful chat
            published_context = geminidataanalytics.Context()
            published_context.system_instruction = "Table incidents and image_reports contains information about bus stop incidents. and field resolved indicate if there is an open incident that required mantainence. \
                                                    Table bus_stops  contain information address, city ,etc for bus stops. \
                                                    When refering to descriptions of the incidents this information should be in table image_reports"
            published_context.datasource_references = datasource_references
            # Optional: To enable advanced analysis with Python, include the following line:
            published_context.options.analysis.python.enabled = True

            data_agent = geminidataanalytics.DataAgent()
            data_agent.data_analytics_agent.published_context = published_context
            data_agent.name = agent_name # Optional
        

            request = geminidataanalytics.CreateDataAgentRequest(
                parent=parent_agent_name,
                data_agent_id=agent_id, # Optional
                data_agent=data_agent,
            )
            
            data_agent_client.create_data_agent(request=request)
            logger.info(f"Data Agent created: {agent_name}")
    except Exception as e:
        logger.error(f"Error creating Data Agent: %s", str(e))



def create_ca_conversation(agent_name:str,parent_agent_name:str,conversation_name:str,conversation_id) -> None:

    try:
         #create now the conversation
        conversation = geminidataanalytics.Conversation()
        data_chat_client = geminidataanalytics.DataChatServiceClient()

        conversation.agents =  [agent_name]
        conversation.name = conversation_name
        request = geminidataanalytics.CreateConversationRequest(
            parent=parent_agent_name,
            conversation_id=conversation_id,
            conversation=conversation,
        )
        # Make the request to create the conversation
        response = data_chat_client.create_conversation(request=request)
        logger.info("Conversation created: %s", str(response))
    except Exception as e:
        logger.error(f"Error creating Data Agent: %s", str(e))

        

def setup_before_agent_call(callback_context: CallbackContext) -> None:
    """Setup the agent and conversation """
    if "conversation_name" not in callback_context.state:
        billing_project =configs.CLOUD_PROJECT
        data_agent_id = configs.CA_API_AGENT_ID 

        conversation_id = callback_context.invocation_id
        callback_context.state["conversation_id"] = conversation_id
        conversation_name =  f"projects/{billing_project}/locations/global/conversations/{conversation_id}"
        callback_context.state["conversation_name"] =conversation_name
        
        callback_context.state["agent_id"] = data_agent_id
        parent_agent_name = f"projects/{billing_project}/locations/global"
        agent_name = f"{parent_agent_name}/dataAgents/{data_agent_id}"

        callback_context.state["agent_parent"] = parent_agent_name
        callback_context.state["agent_name"] =  agent_name

        create_ca_agent(parent_agent_name,data_agent_id, agent_name,billing_project)

        create_ca_conversation(agent_name,parent_agent_name,conversation_name,conversation_id)


tools = [ask_lakehouse,
            get_image_from_bucket,
            analytics_chart_tool,
            get_external_url_image,]

if configs.use_mcp_toolbox:
    if not configs.mcp_toolbox_uri:
        raise ValueError(
            "mcp_toolbox_uri must be set when use_mcp_toolbox is set to True.")
    toolbox = ToolboxSyncClient(configs.mcp_toolbox_uri)
    # Load all the tools
    toolbox_toolset = toolbox.load_toolset('forecast_passangers')
    tools = tools + toolbox_toolset



root_agent = Agent(
    name="maintenance_explorer",
    model=configs.root_agent_settings.model,
    description=configs.root_agent_settings.description,
    global_instruction=GLOBAL_INSTRUCTION,
    planner=BuiltInPlanner(
        thinking_config=ThinkingConfig(include_thoughts=configs.show_thoughts)),
 
    instruction= INSTRUCTION,
    tools=tools,
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.01),
)