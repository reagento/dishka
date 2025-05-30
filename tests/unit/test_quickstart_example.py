import runpy
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent.resolve()
QUICKSTART_EXAMPLE_PATH = ROOT / "docs/quickstart_example.py"


def test_readme_example():
    runpy.run_path(QUICKSTART_EXAMPLE_PATH)
