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


async def ask_report_to_oyen(chat_prompt: str ) -> str:
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
            max_length=4096,
            max_new_tokens=700,  # Réduit pour plus de vitesse
            do_sample=False,
            temperature=0.2,  # Réduit pour plus de cohérence
            num_beams=4,  # Conservé pour un bon compromis qualité/vitesse
            early_stopping=True,  # Ajouté pour arrêter la génération lorsque c'est possible
            length_penalty=0.6,  # Pénalité pour éviter des phrases trop longues
            no_repeat_ngram_size=3,  # Évite les répétitions
            repetition_penalty=1.2,  # Pénalité pour les répétitions
            min_length = 500
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
