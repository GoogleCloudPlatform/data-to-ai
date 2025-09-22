import datetime
import logging
import os
import re
from ..config import Config
from google.protobuf.json_format import MessageToDict
import altair as alt
import proto
from google.adk.tools import FunctionTool, ToolContext
from google.genai import types
from google.cloud import storage
import io


from google.cloud import geminidataanalytics
data_chat_client = geminidataanalytics.DataChatServiceClient()

configs = Config()




ADK_ARTIFACT_FILENAME = "property_image.jpg"
IMAGE_MIME_TYPE = "image/jpg"  # Ensure this matches your image type


from google.adk.tools import FunctionTool, ToolContext
from google.cloud import geminidataanalytics
from google.genai.types import Part, Blob
from google.protobuf.json_format import MessageToDict
import altair as alt
import proto
from io import BytesIO
from typing import Dict, Any

# Define the ADK Function Tool (Must be async since client.chat streams)
async def query_and_save_chart(
    question: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """
    Queries the Conversational Analytics API, extracts chart data (Vega-Lite), 
    renders it as a PNG, and saves the image to ADK artifact storage.
    """
    try:
        # --- 1. Your Existing API Call Logic ---
        input_message = [geminidataanalytics.Message(
            user_message=geminidataanalytics.UserMessage(text=question)
        )]
        
        # Ensure 'agent_parent' is available in context (e.g., from agent setup)
        parent_name = tool_context.state["agent_parent"]
        data_agent_id = tool_context.state["agent_name"]
        
        billing_project =configs.CLOUD_PROJECT
        location = configs.CLOUD_LOCATION
        conversation_id= tool_context.state["conversation_name"]

        # Create a conversation_reference
        conversation_reference = geminidataanalytics.ConversationReference()
        conversation_reference.conversation = conversation_id
        conversation_reference.data_agent_context.data_agent = data_agent_id
        # conversation_reference.data_agent_context.credentials = credentials

        client = geminidataanalytics.DataChatServiceClient()
        request = geminidataanalytics.ChatRequest(
            messages=input_message,
            parent=parent_name,
            conversation_reference=conversation_reference, # messages field expects a list
        )
        # Use a synchronous client.chat call within an async function
        stream = client.chat(request=request)

        chart_data = None
        # --- 2. Process the Streaming Response ---
        for reply in stream:
            if reply.system_message and reply.system_message.chart:
                if "result" in reply.system_message.chart:
                    # --- 3. Extract and Render the Chart ---
                    # Function to safely convert protobuf map/composite types to Python dicts
                    def _convert_proto(v):
                        if isinstance(v, proto.marshal.collections.maps.MapComposite):
                            return {k: _convert_proto(v) for k, v in v.items()}
                        elif isinstance(v, proto.marshal.collections.RepeatedComposite):
                            return [_convert_proto(el) for el in v]
                        elif isinstance(v, (int, float, str, bool)):
                            return v
                        else:
                            return MessageToDict(v)

                    # Extract the Vega-Lite specification
                    vega_config = _convert_proto(reply.system_message.chart.result.vega_config)
                    
                    # Use Altair to create the chart object from the Vega-Lite spec
                    chart = alt.Chart.from_dict(vega_config)

                    # Save the chart as a PNG to an in-memory buffer
                    buffer = BytesIO()
                    chart.save(buffer, format='png')
                    buffer.seek(0)
                    chart.display()

                    # --- 4. Save the PNG to ADK Artifacts ---
                    
                    # Create the ADK Part object for binary data
                    chart_artifact = Part(
                        inline_data=Blob(
                            mime_type="image/png",
                            data=buffer.read()
                        )
                    )
                    
                    # Define a dynamic filename
                    filename = f"analytics_chart.png"
                    
                    # Save the artifact using the ToolContext (must use await)
                    version = await tool_context.save_artifact(
                        filename=filename,
                        artifact=chart_artifact
                    )
                    
                    # --- 5. Return the Result ---
                    return {
                        "status": "success",
                        "message": "Chart successfully generated and saved to session artifacts.",
                        "filename": filename,
                        "version": version
                    }

        
        return {"status": "warning", "message": "Query successful, but no chart data was returned by the API."}

    except Exception as e:
        print(e)
        adas
        return {"status": "exception", "error": f"An error occurred during chart processing: {e}"}

# Final ADK Function Tool definition
analytics_chart_tool = FunctionTool(func=query_and_save_chart)


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


# Initialize GCS client (Authenticates using Application Default Credentials)
gcs_client = storage.Client()

async def save_image_from_gcs(
    gs_uri: str, 
    tool_context: ToolContext ) -> dict:
    """
    1. Reads image data from GCS.
    2. Saves the image data as an ADK artifact.
    """
    try:
        # 1. Download the image blob from GCS
        print(f"Attempting to download {gs_uri} from GCS bucket...")
        if not gs_uri.startswith("gs://"):
                raise ValueError("Invalid GCS URI format. Must start with 'gs://'")
            # Remove the "gs://" prefix
        path_without_prefix = gs_uri[len("gs://"):]
                # Split the path into bucket and object parts
        parts = path_without_prefix.split("/", 1)
        if len(parts) < 2:
                raise ValueError("Invalid GCS URI format. Must include bucket and object.")
        
#         parts = path_without_prefix.split("/", 1)

#         path_without_prefix = gs_uri[len("gs://"):]
#              # Split the path into bucket and object parts
#         parts = path_without_prefix.split("/", 1)
#         if len(parts) < 2:
#             raise ValueError("Invalid GCS URI format. Must include bucket and object.")
# bucket_name = gcs_uri.split('/')[2]

        bucket_name = parts[0]
        image_name = parts[1]

        gcs_bucket = gcs_client.bucket(bucket_name)

        gcs_blob = gcs_bucket.blob(image_name)

        if not gcs_blob.exists():
            return {
                "status": "error",
                "message": f"Error: GCS object gs://{bucket_name}/{image_name} not found."
            }

        # Download the content bytes
        image_bytes = gcs_blob.download_as_bytes()
        print(f"Successfully downloaded {len(image_bytes)} bytes.")

        # 2. Create a types.Part object for the artifact
        image_artifact_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=IMAGE_MIME_TYPE
        )

        # 3. Save the Part to the ADK Artifact Service
        # The artifact_service is configured on the ADK Runner.
        version = await tool_context.save_artifact(
            filename=ADK_ARTIFACT_FILENAME,
            artifact=image_artifact_part
        )
        
        # 4. Construct a response that the agent can use to show the image
        return {
            "status": "success",
            "message": f"Image '{ADK_ARTIFACT_FILENAME}' saved to Artifact Service (Version {version}).",
            "image_filename": ADK_ARTIFACT_FILENAME # This name will be displayed in the UI
        }

    except Exception as e:
        print (e)
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {e}"
        }




get_image_from_bucket = FunctionTool(
    save_image_from_gcs,
    #description="Loads a property image from a Google Cloud Storage bucket and saves it as an artifact for display."
)

