import asyncio
import json
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import AsyncGenerator

GENERATED_TESTS_DIR = Path("generated_tests")
RESULTS_FILE = Path("test_results.json")

async def stream_pytest_execution(
    test_files: list[str] | None = None,
    markers: list[str] | None = None,
    target_base_url: str = "http://127.0.0.1:8001",
) -> AsyncGenerator[dict, None]:
    run_batch_id = str(uuid.uuid4())

    cmd = [
        "python3", "-m", "pytest",
        str(GENERATED_TESTS_DIR) if not test_files else " ".join(test_files),
        "--json-report",
        f"--json-report-file={RESULTS_FILE}",
        "--tb=short",
        "-v",
        "--no-header",
        "-p", "no:warnings",
    ]

    if markers:
        marker_expr = " or ".join(markers)
        cmd.extend(["-m", marker_expr])

    env = os.environ.copy()
    env["TARGET_BASE_URL"] = target_base_url
    env["PYTHONUNBUFFERED"] = "1"

    yield {
        "type": "log",
        "level": "INFO",
        "message": f"🚀 Starting test execution — batch {run_batch_id[:8]}",
        "batch_id": run_batch_id
    }
    yield {
        "type": "log",
        "level": "INFO",
        "message": f"📂 Test directory: {GENERATED_TESTS_DIR}",
    }
    yield {
        "type": "log",
        "level": "INFO",
        "message": f"🔗 Target URL: {target_base_url}",
    }
    yield {
        "type": "log",
        "level": "INFO",
        "message": f"⚙️  Command: {' '.join(cmd)}",
    }

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
            cwd=Path.cwd()
        )
    except FileNotFoundError:
        yield {
            "type": "error",
            "message": "❌ pytest not found — make sure it is installed in the venv"
        }
        return

    passed = failed = errors = skipped = 0

    async for raw_line in process.stdout:
        line = raw_line.decode("utf-8", errors="replace").rstrip()
        if not line:
            continue

        level = "INFO"
        if " PASSED" in line:
            level = "SUCCESS"
            passed += 1
        elif " FAILED" in line:
            level = "FAIL"
            failed += 1
        elif " ERROR" in line:
            level = "ERROR"
            errors += 1
        elif " SKIPPED" in line:
            level = "WARN"
            skipped += 1
        elif line.startswith("FAILED") or "AssertionError" in line or "assert " in line:
            level = "FAIL"
        elif line.startswith("E ") or "Error" in line:
            level = "ERROR"
        elif line.startswith("=") or line.startswith("_"):
            level = "DIVIDER"

        yield {
            "type": "log",
            "level": level,
            "message": line,
            "counts": {
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped
            }
        }

    await process.wait()
    exit_code = process.returncode

    test_results = []
    if RESULTS_FILE.exists():
        try:
            report = json.loads(RESULTS_FILE.read_text())
            for test in report.get("tests", []):
                node_id   = test.get("nodeid", "")
                outcome   = test.get("outcome", "unknown")
                duration  = test.get("duration", 0.0)
                longrepr  = test.get("longrepr", "") or test.get("call", {}).get("longrepr", "")

                req_id = None
                tc_id  = None
                parts  = node_id.replace("::", "/").split("/")
                for part in parts:
                    if part.startswith("REQ_"):
                        req_id = part.replace("_", "-", 2).replace("REQ-", "REQ-")
                    if part.startswith("TC_REQ_") or part.startswith("test_TC_"):
                        tc_id = part.replace("test_", "").replace("_", "-", 4).upper()

                test_results.append({
                    "batch_id":       run_batch_id,
                    "req_id":         req_id,
                    "tc_id":          tc_id,
                    "test_name":      node_id,
                    "filename":       parts[0] if parts else "",
                    "status":         outcome,
                    "duration":       round(duration, 3),
                    "error_message":  str(longrepr) if longrepr else None,
                })
        except Exception as e:
            yield {
                "type": "log",
                "level": "WARN",
                "message": f"⚠️  Could not parse JSON report: {e}"
            }

    yield {
        "type": "result",
        "batch_id":    run_batch_id,
        "exit_code":   exit_code,
        "summary": {
            "passed":  passed,
            "failed":  failed,
            "errors":  errors,
            "skipped": skipped,
            "total":   passed + failed + errors + skipped,
        },
        "test_results": test_results,
        "status": "pass" if exit_code == 0 else "fail"
    }

    yield {
        "type": "done",
        "message": (
            f"✅ Execution complete — "
            f"{passed} passed · {failed} failed · {errors} errors · {skipped} skipped"
            if exit_code == 0 else
            f"❌ Execution finished with failures — "
            f"{passed} passed · {failed} failed · {errors} errors · {skipped} skipped"
        )
    }
