import boto3
import json

# Replace with your model ID
model_id = "arn:aws:bedrock:us-east-1:your-account-id:imported-model/your-model-id"

# Prompt to interact with the model
prompt = "Who are you?"

# Initialize the Bedrock Runtime client
client = boto3.client("bedrock-runtime")

# Invoke the model
response = client.invoke_model(
    modelId=model_id,
    body=json.dumps({"prompt": prompt}),
    accept="application/json",
    contentType="application/json",
)

# Parse the response
result = json.loads(response["body"].read().decode("utf-8"))

# Chunk the response to ensure brevity
full_response = result.get("generation", "")
# Extract the first sentence (or first chunk if separated by newlines)
chunked_response = full_response.split(".")[0].strip() + "."

# Print the results
print("DEMO FOR USING A CUSTOM MODEL...")
print(f"PROMPT: {prompt}")
print(f"RESPONSE: {chunked_response}")
