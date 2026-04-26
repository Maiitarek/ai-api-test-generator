import json
from datetime import datetime
from pathlib import Path

SUMMARY_DIR = "reports"


def generate_summary(spec_title: str, endpoints: list, generated_files: list, exit_code: int) -> dict:
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "api_title": spec_title,
        "total_endpoints": len(endpoints),
        "total_test_files_generated": len(generated_files),
        "total_test_cases_generated": len(generated_files) * 3,
        "pytest_status": "PASSED" if exit_code == 0 else "FAILED",
        "generated_files": generated_files,
        "endpoints_covered": [f"{ep['method']} {ep['path']}" for ep in endpoints],
    }


def save_summary(summary: dict, output_dir: str = SUMMARY_DIR):
    Path(output_dir).mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = Path(output_dir) / f"summary_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved: {path}")
    return str(path)


def print_summary(summary: dict):
    print("\n" + "=" * 60)
    print("  AI API TEST SUITE GENERATOR — RUN SUMMARY")
    print("=" * 60)
    print(f"  API             : {summary['api_title']}")
    print(f"  Endpoints found : {summary['total_endpoints']}")
    print(f"  Test files      : {summary['total_test_files_generated']}")
    print(f"  Test cases      : {summary['total_test_cases_generated']} (3 per endpoint)")
    print(f"  Pytest status   : {summary['pytest_status']}")
    print(f"  Timestamp       : {summary['timestamp']}")
    print("=" * 60)
