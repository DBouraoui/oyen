import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, logging

# --- Supprimer les warnings ---
logging.set_verbosity_error()

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
    dtype=torch.bfloat16 if device == "mps" else torch.float16,
    trust_remote_code=True,
    attn_implementation="eager",
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
)

# --- FONCTION DE RAPPORT ---
def ask_report_to_oyen(json_data, max_tokens=150):
    """
    Génère un rapport Markdown en français à partir d'un JSON de stats serveur.

    json_data: dict
    max_tokens: int, longueur max du rapport
    """
    chat_prompt = f"""<|system|>
    You are a helpful assistant that analyzes server metrics.
    You receive JSON data about system health (RAM usage, pings, memory, storage, etc.).
    Your task:
    - Generate a **Markdown report** with the following fixed structure:
        1. A main title: ## Rapport Santé Serveur
        2. A bullet list or table summarizing each metric from the JSON
           (e.g., pings, RAM, memory, storage)
        3. A short analysis section with the title: ### Analyse
        4. One or two improvement recommendations with the title: ### Recommandations
    - Always maintain the same section titles and structure, even if some values are missing.
    - Use French language, concise and clear.
    - Keep the report short, max ~150-200 tokens.

    <|user|>
    Here is the JSON data:
    {json.dumps(json_data, indent=2)}
    <|end|>
    <|assistant|>"""

    output = pipe(
        chat_prompt,
        max_new_tokens=max_tokens,
        return_full_text=False,
        temperature=0.0,
        use_cache=False,
        do_sample=False,
    )

    return output[0]["generated_text"]

# --- EXEMPLE D'UTILISATION ---
if __name__ == "__main__":
    sample_data = {
        "ping_ok": 20,
        "ping_ko": 10,
        "ram_mid": "70%",
        "memory": "67%",
        "stockage": "20%"
    }

    report = ask_report_to_oyen(sample_data)
    print("\n--- RAPPORT SERVER ---\n")
    print(report)
