from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "patch_preparation", ROOT / "tools/diagnostics/prepare_elevenlabs_patches.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PATCHES = ROOT / "docs/pilot_v2_review/tool_patches"


def test_nested_required_and_constants():
    schema = module.convert_schema({"id": "body", "type": "object", "properties": [
        {"id": "ids", "type": "array", "required": True,
         "items": {"id": "item", "type": "integer", "required": False}},
        {"id": "compact", "type": "boolean", "required": True,
         "value_type": "constant", "constant_value": "true"},
    ]})
    assert schema["required"] == ["ids", "compact"]
    assert schema["properties"]["compact"]["constant_value"] == "true"
    assert "required" not in schema["properties"]["ids"]["items"]
    assert "id" not in schema["properties"]["ids"]


def test_duplicate_field_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        module.convert_schema({"type": "object", "properties": [
            {"id": "a", "type": "string"}, {"id": "a", "type": "string"}]})


def test_all_patches_preserve_transport_and_system_tools():
    tools = [{"name": name, "id": name + "_id", "description": "old",
              "assignments": [{"dynamic_variable": "old"}],
              "response_timeout_secs": 30,
              "api_schema": {"url": "https://example.invalid/" + name,
                  "auth_connection": {"secret": "DO-NOT-EXPORT"},
                  "request_headers": {"X-Conversation-Id": {"variable_name": "system__conversation_id"}},
                  "request_body_schema": {"type": "object", "properties": {}, "required": []}}}
             for name in module.TOOL_NAMES]
    tools.append({"name": "transfer_to_number", "type": "system"})
    export = {"conversation_config": {"agent": {"prompt": {"tools": tools}}}}
    before = deepcopy(export)
    patches = module.prepare(export, PATCHES)
    assert export == before
    assert "DO-NOT-EXPORT" not in json.dumps(patches)
    for tool in tools[:-1]:
        merged = module.merge_tool(tool, patches[tool["name"]])
        for key in ("url", "auth_connection", "request_headers"):
            assert merged["api_schema"][key] == tool["api_schema"][key]
        assert merged["id"] == tool["id"]
        assert merged["response_timeout_secs"] == 30
    write = patches["appointment_write"]
    assert next(a for a in write["assignments"] if a["dynamic_variable"] == "write_ok")["value_path"] == "booking_confirmed"
    patient = patches["patient_lookup"]["api_schema"]["request_body_schema"]
    assert "birth_number_last4" not in patient["properties"]
    handoff = patches["handoff_summary"]["api_schema"]["request_body_schema"]
    assert "current_step" not in handoff["properties"]
    assert "conversation_summary" in handoff["required"]


def test_transport_patch_rejected():
    with pytest.raises(ValueError, match="request body"):
        module.merge_tool({}, {"description": "x", "api_schema": {"url": "wrong"}})


@pytest.mark.parametrize("name,needed", [
    ("appointment_write", {"status", "booking_confirmed"}),
    ("patient_lookup", {"status", "verification.verified", "appointments"}),
    ("doctor_availability", {"options_json"}),
    ("handoff_summary", {"summary_for_staff", "reason"}),
])
def test_current_prompt_can_read_required_tool_results(name, needed):
    # The new prompt reads current tool results rather than interpolating the
    # legacy dynamic variables. Removing these fields hides the outcome/history.
    patch = json.loads((PATCHES / (name + ".current_export.patch.json")).read_text(encoding="utf-8"))
    assignments = {a["value_path"]: a for a in patch["assignments"]}
    assert needed <= assignments.keys()
    assert all(assignments[path]["sanitize"] is False for path in needed)
