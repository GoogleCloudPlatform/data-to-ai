import datetime
import logging
import os
import re


from google.adk.tools import ToolContext

from google.cloud import geminidataanalytics
data_chat_client = geminidataanalytics.DataChatServiceClient()


def ask_lakehouse(
    question: str,
    tool_context: ToolContext,
) -> str:
    

    messages = [geminidataanalytics.Message()]
    messages[0].user_message.text = question

    data_agent_id = tool_context.state["data_agent_id"] 
    conversation_id = tool_context.state["conversation_id"]
    billing_project= tool_context.state["billing_project"]
    # Create a conversation_reference
    conversation_reference = geminidataanalytics.ConversationReference()
    conversation_reference.conversation = f"projects/{billing_project}/locations/global/conversations/{conversation_id}"
    conversation_reference.data_agent_context.data_agent = f"projects/{billing_project}/locations/global/dataAgents/{data_agent_id}"
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


