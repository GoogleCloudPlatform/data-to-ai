import vertexai
from maintenance_scheduler.config import Config
# from vertexai.preview.reasoning_engines import AdkApp

configs = Config()

vertexai.init(
    project=configs.CLOUD_PROJECT,
    location=configs.CLOUD_LOCATION
)

# get the agent based on resource id
remote_app = vertexai.agent_engines.get(configs.AGENT_RESOURCE_ID)

session = remote_app.create_session(user_id="123")

for event in remote_app.stream_query(
    user_id="abc",
    session_id=session["id"],
    message="I am looking for some fertilizer. Can you help me?",
):
  print(event)