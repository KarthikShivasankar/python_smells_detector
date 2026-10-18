Deliberately smelly project used by `tests/test_e2e.py` (and handy for agents to
try the CLI on). Every file exists to trigger specific smells; `shop/broken.py`
does not parse on purpose, to exercise the `errors` list of the JSON report.
Do not fix the code here.
