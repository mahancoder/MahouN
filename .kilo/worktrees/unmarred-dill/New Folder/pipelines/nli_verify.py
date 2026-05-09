# pipelines/nli_verify.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from ._config import load_config
from ._logging import setup_logger
from .utils_text import sent_tokenize_simple

log = setup_logger("nli")


def nli_filter(context: str, claim: str, tok, mdl, device, th=0.5) -> bool:
    with torch.no_grad():
        batch = tok(
            claim, context, return_tensors="pt", truncation=True, padding=True, max_length=512
        ).to(device)
        logits = (
            mdl(**batch).logits.softmax(-1).squeeze(0)
        )  # [entail, neutral, contradict] ordering varies by model
        entail_prob = (
            float(logits[2]) if logits.shape[-1] == 3 else float(logits[1])
        )  # adjust if needed
        return entail_prob >= th


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--context_file", required=True)  # فایل متن مستندات ادغام‌شده
    ap.add_argument("--answer_file", required=True)  # خروجی مدل/پاسخ
    ap.add_argument("--out_file", required=True)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--wandb", action="store_true", help="Enable W&B logging")
    args = ap.parse_args()

    # W&B init
    if args.wandb:
        import wandb

        wandb.init(project=os.getenv("WANDB_PROJECT", "mahoun"), name="nli_verify", reinit=True)

    cfg = load_config()
    tok = AutoTokenizer.from_pretrained(cfg.nli_model)
    mdl = (
        AutoModelForSequenceClassification.from_pretrained(cfg.nli_model)
        .eval()
        .to("cuda" if torch.cuda.is_available() else "cpu")
    )

    if args.wandb:
        wandb.config.update({"nli_model": cfg.nli_model, "threshold": args.threshold})

    ctx = open(args.context_file, "r", encoding="utf-8").read()
    ans = open(args.answer_file, "r", encoding="utf-8").read()

    total_sents = sent_tokenize_simple(ans)
    kept = []
    for sent in total_sents:
        if nli_filter(ctx, sent, tok, mdl, mdl.device, th=args.threshold):
            kept.append(sent)

    with open(args.out_file, "w", encoding="utf-8") as w:
        w.write(" ".join(kept))

    retention_rate = (len(kept) / len(total_sents) * 100) if total_sents else 0
    log.info(f"NLI kept {len(kept)} / {len(total_sents)} sentences ({retention_rate:.1f}%).")

    if args.wandb:
        wandb.log(
            {
                "total_sentences": len(total_sents),
                "kept_sentences": len(kept),
                "filtered_sentences": len(total_sents) - len(kept),
                "retention_rate": retention_rate,
                "status": "completed",
            }
        )
        wandb.finish()


if __name__ == "__main__":
    main()
