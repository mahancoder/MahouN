# pipelines/extract_ner.py
import os, argparse, json, uuid
from pathlib import Path
from ._config import load_config
from ._logging import setup_logger
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

log = setup_logger("extract_ner")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean_dir", required=True)
    ap.add_argument("--jsonl_out", required=True)
    ap.add_argument("--wandb", action="store_true", help="Enable W&B logging")
    args = ap.parse_args()

    # W&B init
    if args.wandb:
        import wandb

        wandb.init(project=os.getenv("WANDB_PROJECT", "mahoun"), name="extract_ner", reinit=True)

    cfg = load_config()
    log.info(f"Loading NER model: {cfg.ner_model}")
    tok = AutoTokenizer.from_pretrained(cfg.ner_model)
    mdl = AutoModelForTokenClassification.from_pretrained(cfg.ner_model)
    ner = pipeline("ner", model=mdl, tokenizer=tok, aggregation_strategy="simple")

    if args.wandb:
        wandb.config.update({"ner_model": cfg.ner_model})

    out = Path(args.jsonl_out)
    out.parent.mkdir(parents=True, exist_ok=True)

    total_files = 0
    total_entities = 0
    entity_types = {}

    with open(out, "w", encoding="utf-8") as w:
        for fp in Path(args.clean_dir).rglob("*.txt"):
            text = fp.read_text(encoding="utf-8")
            ents = ner(text[:4000])  # safeguard
            groups = {}
            for e in ents:
                label = e["entity_group"]
                groups.setdefault(label, []).append(e["word"])
                entity_types[label] = entity_types.get(label, 0) + 1
                total_entities += 1

            rec = {
                "id": str(uuid.uuid4()),
                "source": str(fp),
                "text": text,
                "meta": {"category": ""},
                "entities": groups,
            }
            w.write(json.dumps(rec, ensure_ascii=False) + "\n")
            total_files += 1

    log.info(f"NER done: {total_entities} entities from {total_files} files.")

    if args.wandb:
        wandb.log(
            {
                "total_files": total_files,
                "total_entities": total_entities,
                "entity_types": entity_types,
                "avg_entities_per_file": total_entities / total_files if total_files > 0 else 0,
                "status": "completed",
            }
        )
        wandb.finish()


if __name__ == "__main__":
    main()
