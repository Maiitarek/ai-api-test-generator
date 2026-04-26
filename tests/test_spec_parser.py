import pytest
import json
import yaml
from src.generator.spec_parser import load_spec, extract_endpoints, summarise_spec


SAMPLE_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0.0"},
    "servers": [{"url": "https://api.test.com"}],
    "paths": {
        "/users": {
            "get": {
                "operationId": "listUsers", "summary": "List all users",
                "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Success"}},
            },
            "post": {
                "operationId": "createUser", "summary": "Create a user",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {
                    "type": "object", "properties": {"name": {"type": "string"}, "email": {"type": "string"}}
                }}}},
                "responses": {"201": {"description": "Created"}},
            },
        },
        "/users/{userId}": {
            "get": {
                "operationId": "getUserById", "summary": "Get user by ID",
                "parameters": [{"name": "userId", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "Success"}, "404": {"description": "Not found"}},
            }
        },
    },
}


@pytest.fixture
def json_spec_file(tmp_path):
    f = tmp_path / "spec.json"
    f.write_text(json.dumps(SAMPLE_SPEC))
    return str(f)


@pytest.fixture
def yaml_spec_file(tmp_path):
    f = tmp_path / "spec.yaml"
    f.write_text(yaml.dump(SAMPLE_SPEC))
    return str(f)


class TestLoadSpec:
    def test_load_json(self, json_spec_file):
        assert load_spec(json_spec_file)["info"]["title"] == "Test API"

    def test_load_yaml(self, yaml_spec_file):
        assert load_spec(yaml_spec_file)["info"]["title"] == "Test API"

    def test_raises_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_spec("nonexistent.yaml")

    def test_raises_unsupported_format(self, tmp_path):
        f = tmp_path / "spec.txt"
        f.write_text("content")
        with pytest.raises(ValueError, match="Unsupported spec format"):
            load_spec(str(f))


class TestExtractEndpoints:
    def test_extracts_correct_count(self):
        assert len(extract_endpoints(SAMPLE_SPEC)) == 3

    def test_required_fields_present(self):
        for ep in extract_endpoints(SAMPLE_SPEC):
            for field in ["path", "method", "operation_id", "parameters", "request_body", "responses", "base_url"]:
                assert field in ep

    def test_methods_uppercase(self):
        for ep in extract_endpoints(SAMPLE_SPEC):
            assert ep["method"] == ep["method"].upper()

    def test_extracts_base_url(self):
        for ep in extract_endpoints(SAMPLE_SPEC):
            assert ep["base_url"] == "https://api.test.com"

    def test_empty_paths(self):
        assert extract_endpoints({"openapi": "3.0.0", "info": {"title": "X"}, "paths": {}}) == []


class TestSummariseSpec:
    def test_contains_title(self):
        assert "Test API" in summarise_spec(SAMPLE_SPEC)

    def test_contains_endpoint_count(self):
        assert "3" in summarise_spec(SAMPLE_SPEC)

    def test_contains_methods(self):
        summary = summarise_spec(SAMPLE_SPEC)
        assert "GET" in summary and "POST" in summary
