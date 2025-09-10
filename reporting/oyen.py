import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, logging

logging.set_verbosity_error()

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Using device: {device}")

try:
    MODEL_NAME = "google/flan-t5-base"
    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_NAME,
        device_map={"": device},
        torch_dtype=torch.bfloat16 if device == "mps" else torch.float32,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    if device == "mps":
        warmup_text = "Texte d'échauffement"
        warmup_inputs = tokenizer(warmup_text, return_tensors="pt").to(device)
        model.generate(**warmup_inputs, max_new_tokens=5)
        torch.mps.empty_cache()

except Exception as e:
    print(f"Erreur lors du chargement du modèle: {e}")
    raise


def ask_report_to_oyen(chat_prompt: str, ) -> str:
    """
    Génère un rapport d'analyse serveur à partir de données JSON
    Version corrigée avec gestion des clés manquantes

    Args:
        json_data: Dictionnaire contenant les métriques serveur

    Returns:
        str: Rapport généré au format Markdown
    """


    inputs = tokenizer(chat_prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_length=512,
            max_new_tokens=300,
            do_sample=False,
            temperature=0.5,
            num_beams=2
        )

    if device == "mps":
        torch.mps.empty_cache()

    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# Exemple d'utilisation (à adapter pour ton routeur FastAPI)
if __name__ == "__main__":
    sample_data = {
        "ping_ok": 20,
        "ping_ko": 5,
        "memory": "65%",
        "storage": "30%",
        "cpu": "45%"
    }

    report = ask_report_to_oyen(sample_data)
    print("\n--- RAPPORT SERVER ---\n")
    print(report)
