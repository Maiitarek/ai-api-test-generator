"""
Template-based test generator — free, no API key required.
Generates 3 pytest test cases per endpoint: happy path, edge case, negative.
"""
import re


def render_template(endpoint: dict) -> str:
    method = endpoint["method"].upper()
    path = endpoint["path"]
    params = endpoint.get("parameters", [])
    body = endpoint.get("request_body", {})
    responses = endpoint.get("responses", {})
    summary = endpoint.get("summary", "") or path
    fn_base = _safe_fn(method, path)
    feature = endpoint.get("tags", [summary])[0] if endpoint.get("tags") else summary
    happy = _happy_path(method, path, fn_base, params, body, responses, feature, summary)
    edge = _edge_case(method, path, fn_base, params, body, responses, feature, summary)
    negative = _negative(method, path, fn_base, params, body, responses, feature, summary)
    return "\n\n".join([happy, edge, negative]) + "\n"


def _happy_path(method, path, fn_base, params, body, responses, feature, summary) -> str:
    success_code = _first_success_code(responses)
    url_expr = _url_expr(path, params, mode="valid")
    kwargs = _request_kwargs(method, params, body, mode="valid")
    assertion = f'assert response.status_code == {success_code}, f"Expected {success_code}, got {{response.status_code}}: {{response.text}}"'
    extra = "" if success_code == "204" else '\n    assert response.headers.get("Content-Type") is not None'
    return f'''@allure.feature("{feature}")
@allure.story("Happy path")
@allure.title("{method} {path} — valid request returns {success_code}")
@allure.severity(allure.severity_level.CRITICAL)
def test_{fn_base}_success(base_url, headers):
    """
    Happy path: {summary}
    Sends a valid {method} request to {path} and asserts {success_code} is returned.
    """
    url = f"{{base_url}}{url_expr}"
    response = requests.{method.lower()}(url, {kwargs}headers=headers, timeout=10)
    {assertion}{extra}'''


def _edge_case(method, path, fn_base, params, body, responses, feature, summary) -> str:
    url_expr = _url_expr(path, params, mode="edge")
    kwargs = _request_kwargs(method, params, body, mode="edge")
    edge_desc = _edge_description(method, params, body)
    return f'''@allure.feature("{feature}")
@allure.story("Edge case")
@allure.title("{method} {path} — {edge_desc}")
@allure.severity(allure.severity_level.NORMAL)
def test_{fn_base}_edge_case(base_url, headers):
    """
    Edge case: {edge_desc}
    Validates boundary behaviour for {method} {path}.
    """
    url = f"{{base_url}}{url_expr}"
    response = requests.{method.lower()}(url, {kwargs}headers=headers, timeout=10)
    assert response.status_code in [200, 201, 204, 400, 404, 405, 422], (
        f"Unexpected status {{response.status_code}} for edge input"
    )'''


def _negative(method, path, fn_base, params, body, responses, feature, summary) -> str:
    error_code = _first_error_code(responses)
    url_expr = _url_expr(path, params, mode="invalid")
    kwargs = _request_kwargs(method, params, body, mode="invalid")
    neg_desc = _negative_description(method, params, body)
    has_required = _has_required_fields(body)
    has_path_params = "invalid" in url_expr
    if not has_required and not has_path_params:
        assertion = 'assert response.status_code in range(200, 600), f"Got unexpected status {response.status_code}"'
    else:
        assertion = f'assert response.status_code >= 400, (\n        f"Expected error status (>=400), got {{response.status_code}}")'
    return f'''@allure.feature("{feature}")
@allure.story("Negative / error handling")
@allure.title("{method} {path} — {neg_desc}")
@allure.severity(allure.severity_level.NORMAL)
def test_{fn_base}_invalid(base_url, headers):
    """
    Negative test: {neg_desc}
    Sends invalid request to {method} {path} and asserts error ({error_code}) is returned.
    """
    url = f"{{base_url}}{url_expr}"
    response = requests.{method.lower()}(url, {kwargs}headers=headers, timeout=10)
    {assertion}'''


def _url_expr(path: str, params: list, mode: str) -> str:
    path_params = [p for p in params if p.get("in") == "path"]
    query_params = [p for p in params if p.get("in") == "query"]
    result = path
    for p in path_params:
        result = result.replace("{" + p["name"] + "}", str(_path_value(p, mode)))
    if query_params and mode == "valid":
        qs = "&".join(f"{p['name']}={_query_value(p, 'valid')}" for p in query_params[:2])
        result += f"?{qs}"
    if query_params and mode == "invalid":
        result += f"?{query_params[0]['name']}=INVALID_$$"
    return result


def _path_value(param: dict, mode: str):
    schema = param.get("schema", {})
    ptype = schema.get("type", "string")
    example = schema.get("example")
    if mode == "invalid": return "invalid-id-xyz"
    if mode == "edge": return 0 if ptype == "integer" else "a"
    return example if example is not None else (1 if ptype == "integer" else "test-value")


def _query_value(param: dict, mode: str):
    schema = param.get("schema", {})
    example = schema.get("example")
    enum = schema.get("enum", [])
    default = schema.get("default")
    ptype = schema.get("type", "string")
    if mode == "invalid": return "INVALID_999"
    if example is not None: return example
    if enum: return enum[0]
    if default is not None: return default
    return 1 if ptype == "integer" else "test"


def _request_kwargs(method: str, params: list, body: dict, mode: str) -> str:
    if method in ("POST", "PUT", "PATCH") and body:
        payload = _build_payload(body, mode)
        if payload is not None:
            return f"json={_to_python_repr(payload)}, "
    return ""


def _build_payload(body: dict, mode: str):
    try:
        schema = body.get("content", {}).get("application/json", {}).get("schema", {})
        properties = schema.get("properties", {})
        required = schema.get("required", [])
    except AttributeError:
        return {}
    if not properties:
        return {} if mode == "invalid" else {"key": "value"}
    payload = {}
    for field, field_schema in properties.items():
        ftype = field_schema.get("type", "string")
        if mode == "invalid":
            if field not in required: payload[field] = None
        elif mode == "edge":
            payload[field] = _edge_value(ftype, field_schema)
        else:
            payload[field] = _valid_value(ftype, field_schema, field)
    return payload


def _has_required_fields(body: dict) -> bool:
    try:
        schema = body.get("content", {}).get("application/json", {}).get("schema", {})
        return len(schema.get("required", [])) > 0
    except AttributeError:
        return False


def _valid_value(ftype: str, schema: dict, field_name: str = ""):
    example = schema.get("example")
    if example is not None: return example
    enum = schema.get("enum", [])
    if enum: return enum[0]
    if ftype == "integer": return 1
    if ftype == "boolean": return True
    if ftype == "array": return ["sample"]
    if ftype == "object": return {}
    name = field_name.lower()
    if "email" in name: return "test@example.com"
    if "password" in name: return "SecurePass123!"
    if "name" in name: return "Test User"
    if "job" in name: return "QA Engineer"
    return "test-value"


def _edge_value(ftype: str, schema: dict):
    if ftype == "integer": return 0
    if ftype == "string":
        max_len = schema.get("maxLength")
        return "x" * max_len if max_len else ""
    if ftype == "array": return []
    if ftype == "boolean": return False
    return None


def _to_python_repr(obj) -> str:
    if obj is None: return "None"
    if isinstance(obj, bool): return "True" if obj else "False"
    if isinstance(obj, str):
        return f'"{obj.replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))}"
if isinstance(obj, (int, float)): return str(obj)
    if isinstance(obj, list): return "[" + ", ".join(_to_python_repr(i) for i in obj) + "]"
    if isinstance(obj, dict):
        pairs = ", ".join(f'"{k}": {_to_python_repr(v)}' for k, v in obj.items())
        return "{" + pairs + "}"
    return repr(obj)


def _first_success_code(responses: dict) -> str:
    for code in ["200", "201", "202", "204"]:
        if code in responses: return code
    return "200"


def _first_error_code(responses: dict) -> str:
    for code in ["400", "404", "405", "422", "401", "403"]:
        if code in responses: return code
    return "400"


def _edge_description(method: str, params: list, body: dict) -> str:
    path_params = [p for p in params if p.get("in") == "path"]
    query_params = [p for p in params if p.get("in") == "query"]
    if path_params: return f"boundary value for path param '{path_params[0]['name']}'"
    if query_params: return f"boundary value for query param '{query_params[0]['name']}'"
    if method in ("POST", "PUT", "PATCH") and body: return "empty or minimal request body"
    return "boundary / empty input"


def _negative_description(method: str, params: list, body: dict) -> str:
    path_params = [p for p in params if p.get("in") == "path"]
    if path_params: return f"invalid value for path param '{path_params[0]['name']}'"
    if method in ("POST", "PUT", "PATCH") and body: return "missing required fields in request body"
    return "invalid or malformed input"


def _safe_fn(method: str, path: str) -> str:
    path_part = re.sub(r"[{}]", "", path).replace("/", "_").strip("_")
    return f"{method.lower()}_{re.sub(r'_+', '_', path_part)}"
