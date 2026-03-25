import os
import json
from pathlib import Path
from datetime import datetime

GENERATED_TESTS_DIR = Path("generated_tests")


def ensure_output_dir():
    GENERATED_TESTS_DIR.mkdir(parents=True, exist_ok=True)
    # Create conftest.py if it doesn't exist
    conftest = GENERATED_TESTS_DIR / "conftest.py"
    if not conftest.exists():
        conftest.write_text(
            "# Auto-generated conftest — add shared fixtures here\n"
            "import pytest\n"
            "import os\n\n"
            "def pytest_configure(config):\n"
            "    config.addinivalue_line('markers', 'positive: positive test cases')\n"
            "    config.addinivalue_line('markers', 'negative: negative test cases')\n"
            "    config.addinivalue_line('markers', 'edge: edge case tests')\n"
            "    config.addinivalue_line('markers', 'api: API tests')\n"
            "    config.addinivalue_line('markers', 'ui: UI tests')\n"
            "    config.addinivalue_line('markers', 'etl: ETL tests')\n"
            "    config.addinivalue_line('markers', 'performance: performance tests')\n"
        )


def write_test_file(filename: str, code: str) -> str:
    """Write generated test code to disk. Returns full file path."""
    ensure_output_dir()
    filepath = GENERATED_TESTS_DIR / filename
    filepath.write_text(code, encoding="utf-8")
    return str(filepath)


def write_manifest(test_files: list[dict]) -> str:
    """Write a manifest JSON listing all generated files."""
    ensure_output_dir()
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_files": len(test_files),
        "files": [
            {
                "req_id": f["req_id"],
                "filename": f["filename"],
                "frameworks": f["frameworks_used"],
                "filepath": str(GENERATED_TESTS_DIR / f["filename"])
            }
            for f in test_files
        ]
    }
    manifest_path = GENERATED_TESTS_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return str(manifest_path)
