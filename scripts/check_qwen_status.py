from transformers import AutoTokenizer
from huggingface_hub import try_to_load_from_cache

model_id = "Qwen/Qwen2.5-1.5B-Instruct"

print(f"Checking model: {model_id}")

try:
    # Check if model config is in cache
    cached_config = try_to_load_from_cache(repo_id=model_id, filename="config.json")
    if cached_config:
        print(f"Config found in cache: {cached_config}")
    else:
        print("Config NOT found in cache.")

    # Try loading with local_files_only to confirm
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
        print("Tokenizer loaded successfully from local cache.")

        # Just check for model existence, don't load full weights to save time/ram
        model_cached = try_to_load_from_cache(
            repo_id=model_id, filename="model.safetensors"
        ) or try_to_load_from_cache(repo_id=model_id, filename="pytorch_model.bin")

        if model_cached:
            print(f"Model weights found in cache: {model_cached}")
        else:
            print("Model weights NOT found in cache.")

    except Exception as e:
        print(f"Failed to load local only: {e}")

except Exception as e:
    print(f"Error checking cache: {e}")
