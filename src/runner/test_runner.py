import subprocess
import sys
from pathlib import Path


def run_pytest(test_dir: str = "generated_tests", allure_results_dir: str = "allure-results") -> int:
    test_path = Path(test_dir)
    if not test_path.exists() or not any(test_path.glob("test_*.py")):
        print(f"No test files found in {test_dir}/")
        return 1
    cmd = [sys.executable, "-m", "pytest", str(test_path),
           f"--alluredir={allure_results_dir}", "-v", "--tb=short", "--no-header"]
    print(f"\nRunning: {' '.join(cmd)}\n")
    return subprocess.run(cmd).returncode


def open_allure_report(allure_results_dir: str = "allure-results"):
    try:
        subprocess.run(["allure", "serve", allure_results_dir], check=True)
    except FileNotFoundError:
        print("Allure CLI not found. Install: npm install -g allure-commandline")
        print(f"Then: allure serve {allure_results_dir}")
