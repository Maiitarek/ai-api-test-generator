import json
import yaml
from pathlib import Path


def load_spec(spec_path: str) -> dict:
    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        elif path.suffix == ".json":
            return json.load(f)
        else:
            raise ValueError(f"Unsupported spec format: {path.suffix}. Use .json or .yaml")


def extract_endpoints(spec: dict) -> list:
    endpoints = []
    paths = spec.get("paths", {})
    base_info = spec.get("info", {})
    servers = spec.get("servers", [{}])
    base_url = servers[0].get("url", "") if servers else ""
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                continue
            endpoints.append({
                "path": path,
                "method": method.upper(),
                "operation_id": operation.get("operationId", f"{method}_{path.replace('/', '_')}"),
                "summary": operation.get("summary", ""),
                "description": operation.get("description", ""),
                "parameters": operation.get("parameters", []),
                "request_body": operation.get("requestBody", {}),
                "responses": operation.get("responses", {}),
                "tags": operation.get("tags", []),
                "base_url": base_url,
                "api_title": base_info.get("title", "API"),
            })
    return endpoints


def summarise_spec(spec: dict) -> str:
    info = spec.get("info", {})
    endpoints = extract_endpoints(spec)
    lines = [
        f"API: {info.get('title', 'Unknown')}",
        f"Version: {info.get('version', 'Unknown')}",
        f"Total endpoints: {len(endpoints)}", "", "Endpoints:",
    ]
    for ep in endpoints:
        lines.append(f"  {ep['method']} {ep['path']} — {ep['summary'] or ep['operation_id']}")
    return "\n".join(lines)
