# FILE TO DOWNLOAD CORE FILES FOR THE REQUIRED AI-MODEL (LOCALLY)
from huggingface_hub import snapshot_download

MODEL_VENDOR = "deepseek-ai"
MODEL_NAME = "DeepSeek-R1-Distill-Llama-8B"

model_id = f"{MODEL_VENDOR}/{MODEL_NAME}"
local_dir = snapshot_download(
    repo_id=model_id,
    local_dir="model",
)
