import weaviate
from weaviate.classes.init import Auth

# Best practice: store your credentials in environment variables
weaviate_api_key = "user-a-key"
client = weaviate.connect_to_local(
    auth_credentials=Auth.api_key(weaviate_api_key)
)

print(client.is_ready())

assert client.is_ready()

client.close() 