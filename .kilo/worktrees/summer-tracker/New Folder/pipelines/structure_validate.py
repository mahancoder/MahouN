# pipelines/structure_validate.py
import os, argparse, json
from fastjsonschema import compile as compile_schema
from ._logging import setup_logger

log = setup_logger("validate")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True)
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--wandb", action="store_true", help="Enable W&B logging")
    args = ap.parse_args()

    # W&B init
    if args.wandb:
        import wandb

        wandb.init(project=os.getenv("WANDB_PROJECT", "mahoun"), name="validate", reinit=True)

    schema = json.load(open(args.schema, "r", encoding="utf-8"))
    validator = compile_schema(schema)

    ok = bad = 0
    errors = []

    for i, line in enumerate(open(args.jsonl, "r", encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            validator(json.loads(line))
            ok += 1
        except Exception as e:
            bad += 1
            error_msg = f"line={i} err={e}"
            log.error(error_msg)
            if bad <= 10:  # فقط 10 خطای اول
                errors.append(error_msg)

    total = ok + bad
    success_rate = (ok / total * 100) if total > 0 else 0

    log.info(f"Validated: ok={ok} bad={bad} total={total} ({success_rate:.1f}% valid)")

    if args.wandb:
        wandb.log(
            {
                "valid_records": ok,
                "invalid_records": bad,
                "total_records": total,
                "success_rate": success_rate,
                "sample_errors": errors[:5],
                "status": "completed",
            }
        )
        wandb.finish()


if __name__ == "__main__":
    main()
