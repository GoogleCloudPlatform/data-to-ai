import datetime
import logging
import os
import re
from ..config import Config


from google.adk.tools import ToolContext

from google.cloud import geminidataanalytics
data_chat_client = geminidataanalytics.DataChatServiceClient()

configs = Config()

async def  ask_lakehouse(
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

def get_image_from_bucket( gs_uri: str) -> str:
        """
        Retrieves the public URL of an image from a Google Cloud Storage bucket.

        Args:
            gs_uri (str): uri to the image in a bucket
        Returns:
            str: The public URL of the image, or an error message if not found or accessible.
        """
        try: 
            if not gs_uri.startswith("gs://"):
                raise ValueError("Invalid GCS URI format. Must start with 'gs://'")
            # Remove the "gs://" prefix
            path_without_prefix = gs_uri[len("gs://"):]
            # Split the path into bucket and object parts
            parts = path_without_prefix.split("/", 1)
            if len(parts) < 2:
                raise ValueError("Invalid GCS URI format. Must include bucket and object.")
            bucket_name = parts[0]
            object_name = parts[1]

            # Construct the HTTPS URL
            https_url = f"https://storage.cloud.google.com/{bucket_name}/{object_name}"
            return https_url
        except Exception as e:
            return f"An error occurred while retrieving the image from GCS: {e}"
