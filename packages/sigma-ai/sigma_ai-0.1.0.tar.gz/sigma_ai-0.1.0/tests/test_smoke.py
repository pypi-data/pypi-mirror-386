from sigma_ai.eval.runner import run_suite
def test_smoke():
    r = run_suite("tests/t3000.tsv", "openai", max_examples=1)
    assert r["status"] == "ok"
