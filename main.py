#!/usr/bin/env python3
"""
AI API Test Suite Generator
Usage:
    python main.py --spec sample_specs/local_mock.yaml
    python main.py --spec your_api.yaml --mode ai
    python main.py --spec your_api.yaml --no-run
    python main.py --spec your_api.yaml --clean
"""
import argparse
import os
import sys
from dotenv import load_dotenv
from src.generator.spec_parser import load_spec, extract_endpoints, summarise_spec
from src.generator.test_generator import generate_all_tests
from src.runner.file_writer import write_generated_tests, clean_generated_tests
from src.runner.test_runner import run_pytest, open_allure_report
from src.reporter.report_builder import generate_summary, save_summary, print_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Generate and run API tests from an OpenAPI spec.")
    parser.add_argument("--spec", required=True, help="Path to OpenAPI spec (.json or .yaml)")
    parser.add_argument("--mode", choices=["template", "ai"], default="template")
    parser.add_argument("--no-run", action="store_true", help="Generate only, skip pytest")
    parser.add_argument("--clean", action="store_true", help="Clean previous generated tests")
    parser.add_argument("--open-report", action="store_true", help="Open Allure report after run")
    parser.add_argument("--output-dir", default="generated_tests")
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()
    api_key = None
    if args.mode == "ai":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("\nERROR: --mode ai requires ANTHROPIC_API_KEY.")
            print("  Copy .env.example to .env and add your key.")
            print("  Or use the free template mode: python main.py --spec your_api.yaml")
            sys.exit(1)
    print(f"\nLoading spec: {args.spec}")
    spec = load_spec(args.spec)
    endpoints = extract_endpoints(spec)
    spec_title = spec.get("info", {}).get("title", "Unknown API")
    print(f"\n{summarise_spec(spec)}")
    print(f"\nFound {len(endpoints)} endpoint(s).")
    print(f"Mode: {'AI-powered (Claude)' if args.mode == 'ai' else 'Template-based (free)'}")
    if not endpoints:
        print("No endpoints found. Exiting.")
        sys.exit(0)
    if args.clean:
        clean_generated_tests(args.output_dir)
    print("\nGenerating tests...")
    test_code_map = generate_all_tests(endpoints, mode=args.mode, api_key=api_key)
    base_url = spec.get("servers", [{}])[0].get("url", "https://api.example.com")
    generated_files = write_generated_tests(test_code_map, base_url, args.output_dir)
    print(f"\n{len(generated_files)} test file(s) written to {args.output_dir}/")
    exit_code = 0
    if not args.no_run:
        print("\nRunning generated tests with pytest + Allure...")
        exit_code = run_pytest(args.output_dir)
        if args.open_report:
            open_allure_report()
    summary = generate_summary(spec_title, endpoints, generated_files, exit_code)
    save_summary(summary)
    print_summary(summary)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
