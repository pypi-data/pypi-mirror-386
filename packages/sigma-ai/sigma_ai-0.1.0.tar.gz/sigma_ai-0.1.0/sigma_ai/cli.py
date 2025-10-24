import argparse
from .eval.runner import run_suite
from .eval.report import save_run

def main():
    p = argparse.ArgumentParser(prog="sigma", description="Sigma-AI benchmark CLI (minimal)")
    p.add_argument("task_file")
    p.add_argument("provider")
    p.add_argument("model", nargs="?")  
    p.add_argument("--out-dir", default="artifacts/demo")
    p.add_argument("--max-examples", type=int, default=0)
    p.add_argument("--judge")
    args = p.parse_args()
    run = run_suite(args.task_file, args.provider, max_examples=args.max_examples, judge=args.judge)
    save_run(run, args.out_dir)
    print(f"Saved results to {args.out_dir}/metrics.json")

if __name__ == "__main__":
    main()
