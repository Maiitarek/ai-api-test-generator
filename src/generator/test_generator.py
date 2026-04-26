import json


SYSTEM_PROMPT = """You are a senior QA automation engineer. Generate pytest test cases for API endpoints.
Rules: 3 test types (happy path, edge case, negative), use requests library, allure decorators,
pytest fixtures. Return ONLY valid Python code, no markdown."""


def build_prompt(endpoint: dict) -> str:
    return f"""Generate pytest tests for: {endpoint['method']} {endpoint['path']}
Summary: {endpoint.get('summary', '')}
Parameters: {json.dumps(endpoint.get('parameters', []))}
Request Body: {json.dumps(endpoint.get('request_body', {}))}
Responses: {json.dumps(endpoint.get('responses', {}))}
Base URL: {endpoint.get('base_url', 'https://api.example.com')}
Generate 3 functions: _success, _edge_case, _invalid. Return only Python code."""


def generate_tests_ai(endpoint: dict, api_key: str, model: str = "claude-sonnet-4-20250514") -> str:
    try:
        import anthropic
    except ImportError:
        raise ImportError("Run: pip install anthropic")
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(model=model, max_tokens=1000, system=SYSTEM_PROMPT,
                                  messages=[{"role": "user", "content": build_prompt(endpoint)}])
    return msg.content[0].text


def generate_tests_template(endpoint: dict) -> str:
    from src.generator.template_engine import render_template
    return render_template(endpoint)


def generate_all_tests(endpoints: list, mode: str = "template", api_key: str = None) -> dict:
    if mode == "ai" and not api_key:
        raise ValueError("mode='ai' requires ANTHROPIC_API_KEY")
    results = {}
    for i, endpoint in enumerate(endpoints):
        print(f"  [{i+1}/{len(endpoints)}] {endpoint['method']} {endpoint['path']} ({mode} mode)")
        try:
            code = generate_tests_ai(endpoint, api_key) if mode == "ai" else generate_tests_template(endpoint)
            results[build_filename(endpoint)] = code
        except Exception as e:
            print(f"    ERROR: {e}")
    return results


def build_filename(endpoint: dict) -> str:
    path_part = endpoint["path"].replace("/", "_").replace("{", "").replace("}", "").strip("_")
    return f"test_{endpoint['method'].lower()}_{path_part}.py"
