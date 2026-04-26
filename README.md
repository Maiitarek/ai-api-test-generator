# AI API Test Suite Generator

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?style=flat&logo=pytest&logoColor=white)](https://pytest.org)
[![Allure](https://img.shields.io/badge/Allure-Report-orange?style=flat)](https://allurereport.org)
[![Claude API](https://img.shields.io/badge/Claude-AI%20Powered-D97757?style=flat)](https://anthropic.com)

An intelligent tool that reads any **OpenAPI / Swagger spec** and automatically generates a complete **pytest test suite** — covering happy path, edge cases, and negative scenarios for every endpoint. Runs the tests and produces an **Allure report** in one command.

## Quick start (free, no API key)

```bash
git clone https://github.com/Maiitarek/ai-api-test-generator.git
cd ai-api-test-generator
pip install -r requirements.txt

# Terminal 1 — start the local mock server
python mock_server.py

# Terminal 2 — generate and run tests
python main.py --spec sample_specs/local_mock.yaml
```

## Two modes

| Mode | Cost | How it works |
|---|---|---|
| `template` (default) | **Free** | Rule-based engine analyses the spec |
| `ai` | Requires Anthropic API key | Claude AI writes the tests |

## Usage

```bash
python main.py --spec sample_specs/local_mock.yaml          # template mode (free)
python main.py --spec your_api.yaml --mode ai                # AI mode
python main.py --spec your_api.yaml --no-run                 # generate only
python main.py --spec your_api.yaml --clean                  # clean + regenerate
```

## What gets generated per endpoint

| Test | What it validates |
|---|---|
| `test_*_success` | Valid input → expected 2xx status |
| `test_*_edge_case` | Boundary values (zero, empty, max) |
| `test_*_invalid` | Missing/invalid input → 4xx error |

## Project structure

```
ai-api-test-generator/
├── src/
│   ├── generator/
│   │   ├── spec_parser.py       # OpenAPI loader and endpoint extractor
│   │   ├── test_generator.py    # Mode router (template vs AI)
│   │   └── template_engine.py  # Rule-based test generation (free)
│   ├── runner/
│   │   ├── file_writer.py      # Writes generated tests to disk
│   │   └── test_runner.py      # Runs pytest programmatically
│   └── reporter/
│       └── report_builder.py   # Builds and saves run summary
├── tests/
│   └── test_spec_parser.py     # Unit tests for the parser
├── sample_specs/
│   ├── local_mock.yaml         # Spec for the local mock server
│   └── petstore.yaml           # Sample Petstore spec
├── mock_server.py              # Local FastAPI mock server
├── main.py                     # CLI entry point
├── pytest.ini                  # pytest + allure config
└── requirements.txt
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Only for `--mode ai` | Your Anthropic API key |
| `BASE_URL` | No | Override base URL from spec |
| `API_TOKEN` | No | Bearer token for auth endpoints |

## Author

**Mai Ibrahim** — Senior SDET / QA Engineer  
[LinkedIn](https://www.linkedin.com/in/mai-tarek/) · [GitHub](https://github.com/Maiitarek)
