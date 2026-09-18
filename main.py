def _flag(args, name):
    return name in args


def _opt(args, name, default=None, cast=str):
    for i, a in enumerate(args):
        if a == name and i + 1 < len(args):
            try:
                return cast(args[i + 1])
            except ValueError:
                return default
    return default


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "explore":
        from src.exploration import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "roles":
        from src.roles import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "conversations":
        from src.conversation import run
        threshold = None
        if len(sys.argv) > 2:
            try:
                threshold = float(sys.argv[2])
            except ValueError:
                print(f"[ERROR] Threshold harus angka, diterima: {sys.argv[2]}")
                return
        run(threshold_hours=threshold)
    elif len(sys.argv) > 1 and sys.argv[1] == "responses":
        from src.client_response import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] == "remote":
        from src.remote import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("category", "categories", "explore-category"):
        from src.category_exploration import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("label", "labeling", "categories-label"):
        from src.category_labeling import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("preprocess", "preprocessing"):
        from src.preprocessing import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("normalize", "normalization"):
        from src.normalization import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("features", "tfidf", "feature-extraction"):
        from src.features import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("split", "train-test-split"):
        from src.split import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("train", "training"):
        from src.train import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("tune", "tuning", "optimize"):
        from src.tuning import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("evaluate", "evaluation", "eval"):
        from src.evaluation import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("select", "selection", "save-best"):
        from src.selection import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("predict", "inference", "prediksi"):
        from src.predict import run
        arg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        run(arg)
    elif len(sys.argv) > 1 and sys.argv[1] in ("consolidate", "consolidation", "combine"):
        from src.consolidation import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("export", "exporting", "report"):
        from src.export import run
        run()
    elif len(sys.argv) > 1 and sys.argv[1] in ("run-all", "pipeline", "retrain", "all"):
        from src.pipeline import run
        arg = sys.argv[2] if len(sys.argv) > 2 else None
        run(arg)
    elif len(sys.argv) > 1 and sys.argv[1] in ("llm-label", "llm_label", "llm3"):
        from src.llm_labeling import run
        rest = sys.argv[2:]
        run(provider=_opt(rest, "--provider"), dry_run=_flag(rest, "--dry-run"))
    elif len(sys.argv) > 1 and sys.argv[1] in ("reconcile", "reconciliation", "recon"):
        from src.reconciliation import run
        rest = sys.argv[2:]
        run(
            provider=_opt(rest, "--provider"),
            dry_run=_flag(rest, "--dry-run"),
            min_samples=_opt(rest, "--min-samples", 5, int),
        )
    elif len(sys.argv) > 1 and sys.argv[1] in ("active-learning", "active", "active-learning-loop"):
        from src.active_learning import run
        rest = sys.argv[2:]
        run(
            provider=_opt(rest, "--provider"),
            dry_run=_flag(rest, "--dry-run"),
            top_n=_opt(rest, "--top-n", 30, int),
        )
    elif len(sys.argv) > 1 and sys.argv[1] in ("train-model", "retrain-model", "llm-train"):
        from src.retrain import run
        rest = sys.argv[2:]
        run(
            label_source=_opt(rest, "--labels", "auto"),
            skip_llm=_flag(rest, "--skip-llm"),
            provider=_opt(rest, "--provider"),
        )
    elif len(sys.argv) > 1 and sys.argv[1] in ("audit-labels", "audit", "audit-ground-truth"):
        from src.audit_labels import run
        rest = sys.argv[2:]
        run(
            input_path=_opt(rest, "--input"),
            limit=_opt(rest, "--limit", None, int),
        )
    else:
        from src.parser import run
        run()


if __name__ == "__main__":
    main()