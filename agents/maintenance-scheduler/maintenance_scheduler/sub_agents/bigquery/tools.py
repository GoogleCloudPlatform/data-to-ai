import datetime
import logging
import os
import re
from ...config import Config


from google.adk.tools import ToolContext

from google.cloud import geminidataanalytics
data_chat_client = geminidataanalytics.DataChatServiceClient()

configs = Config()

def ask_lakehouse(
    question: str,
    tool_context: ToolContext,
) -> str:
    

    messages = [geminidataanalytics.Message()]
    messages[0].user_message.text = question

    agent_name = tool_context.state["agent_name"] 
    conversation_name = tool_context.state["conversation_name"]
    billing_project =configs.CLOUD_PROJECT
    # Create a conversation_reference
    conversation_reference = geminidataanalytics.ConversationReference()
    conversation_reference.conversation = conversation_name
    conversation_reference.data_agent_context.data_agent = agent_name
    # conversation_reference.data_agent_context.credentials = credentials

    # Form the request
    request = geminidataanalytics.ChatRequest(
        parent = f"projects/{billing_project}/locations/global",
        messages = messages,
        conversation_reference = conversation_reference
    )

    # Make the request
    stream = data_chat_client.chat(request=request)
    # Handle the response
    responses = []
    for response in stream:
        responses.append(str(response.system_message))
    
    return responses


