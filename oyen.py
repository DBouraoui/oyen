import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# --- CONFIG ---
MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

# --- DEVICE ---
if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

print(f"Using device: {device}")

# --- LOAD MODEL ---
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map={"": device},
    dtype=torch.float16 if device != "cpu" else torch.float32,
    trust_remote_code=True,
    attn_implementation="eager",
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)

# --- BUILD PROMPT ---
chat_prompt = """<|system|>
You are a helpful assistant that analyzes server metrics.
You receive JSON data about system health (RAM, pings, memory, storage, etc.).
Your task:
1. Generate a clear **Markdown report** with bullet points or tables.
2. Provide a short **analysis** of the situation.
3. Suggest **one or two improvements** if necessary.
4. Return your report in french<|end|>
<|user|>
Here is the JSON data:
{
  "ping_ok": 20,
  "ping_ko": 10,
  "ram_mid": "70%",
  "memory": "67%",
  "stockage": "20%"
}
<|end|>
<|assistant|>"""

output = pipe(
    chat_prompt,
    max_new_tokens=500,
    return_full_text=False,
    temperature=0.3,
    use_cache=False,              # 🔑 force le fallback sans DynamicCache
)

print(output[0]["generated_text"])

