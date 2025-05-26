import vertexai
from maintenance_scheduler.config import Config

configs = Config()

vertexai.init(
    project=configs.CLOUD_PROJECT,
    location=configs.CLOUD_LOCATION
)

# get the agent based on resource id
remote_app = vertexai.agent_engines.get(configs.AGENT_RESOURCE_ID)

user_id = "supervisor"
session = remote_app.create_session(user_id=user_id)

for event in remote_app.stream_query(
    user_id=user_id,
    session_id=session["id"],
    message="Check if there is any bus stop maintenance needed",
):
  print(event)