"""Prepare body-only tool patches; never serialize transport/auth from an export."""
import argparse
from copy import deepcopy
import json
from pathlib import Path


TOOL_NAMES = (
    "agent_capabilities", "doctor_availability", "patient_lookup",
    "appointment_write", "handoff_summary",
)


def convert_schema(node):
    result = {key: deepcopy(value) for key, value in node.items()
              if key not in {"id", "value_type", "required", "properties", "items"}}
    result.setdefault("description", "")
    result.setdefault("dynamic_variable", "")
    result.setdefault("is_omitted", False)
    kind = result.get("type")
    if kind == "object":
        properties = node.get("properties", [])
        if not isinstance(properties, list):
            raise ValueError("Expected legacy properties list")
        converted = {}
        required = []
        for prop in properties:
            name = prop.get("id")
            if not isinstance(name, str) or not name or name in converted:
                raise ValueError("Missing or duplicate property ID")
            converted[name] = convert_schema(prop)
            if prop.get("required") is True:
                required.append(name)
        result.update(properties=converted, required=required)
    elif kind == "array":
        result.setdefault("constant_value", None)
        result["items"] = convert_schema(node["items"])
    elif kind in {"string", "integer", "number", "boolean"}:
        for key, value in {
            "enum": None, "is_system_provided": False,
            "allowed_values": None, "allowed_values_dynamic_variable": "",
            "constant_value": "",
        }.items():
            result.setdefault(key, value)
    else:
        raise ValueError("Unsupported schema type")
    return result


def merge_tool(tool, patch):
    """Explicit replacement at three allowed paths, never a shallow API merge."""
    if set(patch) - {"description", "api_schema", "assignments"}:
        raise ValueError("Unexpected tool patch field")
    if set(patch.get("api_schema", {})) != {"request_body_schema"}:
        raise ValueError("Only the request body schema may be patched")
    merged = deepcopy(tool)
    merged["description"] = patch["description"]
    merged["api_schema"]["request_body_schema"] = deepcopy(
        patch["api_schema"]["request_body_schema"])
    if "assignments" in patch:
        merged["assignments"] = deepcopy(patch["assignments"])
    return merged


def prepare(export, directory):
    tools = export["conversation_config"]["agent"]["prompt"]["tools"]
    indexed = {}
    for tool in tools:
        name = tool["name"]
        if name in indexed:
            raise ValueError("Duplicate tool name in export")
        indexed[name] = tool
    prepared = {}
    for name in TOOL_NAMES:
        tool = indexed[name]
        body = tool["api_schema"]["request_body_schema"]
        if not isinstance(body.get("properties"), dict) or not isinstance(body.get("required"), list):
            raise ValueError("Export is not in the expected dictionary schema format")
        # Handoff's separately reviewed patch is already in the current format.
        suffix = ".current_export.patch.json" if name == "handoff_summary" else ".patch.json"
        patch = json.loads((directory / (name + suffix)).read_text(encoding="utf-8-sig"))
        if name != "handoff_summary":
            patch["api_schema"]["request_body_schema"] = convert_schema(
                patch["api_schema"]["request_body_schema"])
        merged = merge_tool(tool, patch)
        for key, value in tool.items():
            if key not in {"description", "assignments", "api_schema"}:
                assert merged[key] == value
        assert {k: v for k, v in merged["api_schema"].items() if k != "request_body_schema"} == {
            k: v for k, v in tool["api_schema"].items() if k != "request_body_schema"}
        prepared[name] = patch
    return prepared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--patch-dir", type=Path, default=Path(__file__).resolve().parents[2] / "docs/pilot_v2_review/tool_patches")
    args = parser.parse_args()
    export = json.loads(args.export.read_text(encoding="utf-8-sig"))
    prepared = prepare(export, args.patch_dir)
    for name, patch in prepared.items():
        if name != "handoff_summary":
            (args.patch_dir / (name + ".current_export.patch.json")).write_text(
                json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Validated five in-memory merges; wrote four transport-free candidate patches. Nothing published.")


if __name__ == "__main__":
    main()
