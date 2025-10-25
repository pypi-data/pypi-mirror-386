import os
import re
import yaml
import logging

from . import project_service as proj
from . import qsa_parser
from quip import cprint, print_ascii_art2


def generate(q, spec_path: str, dry_run: bool = False):
    """Generate a new extension from a minimal spec and a baseline project.

    Supports two input formats:
    - .yml/.yaml: YAML specification format
    - .qsa: Quip Simple Automation format

    Args:
        q: Quip instance
        spec_path: Path to the spec file
        dry_run: If True, only parse and print YAML without creating project

    Steps:
    - Clone/bootstrap from baseline into new project folder
    - Create fields.yml from minimal spec (ensure Action field exists)
    - Run fields update to apply to template.json
    - Update src/fields/input.py with typed attributes
    - Ensure Action enum in src/fields/enums.py matches items
    - Create stub functions in src/actions/actions.py for each action
    - Update src/extension.py to dispatch based on selected action
    """
    # Show ASCII art branding (skip in dry-run mode)
    if not dry_run:
        print_ascii_art2()

    # Detect file extension and use appropriate parser
    _, file_ext = os.path.splitext(spec_path)
    file_ext = file_ext.lower()

    if file_ext in ('.qsa',):
        # Parse QSA file directly - returns complete fields configuration
        cprint(f"Parsing QSA file: {spec_path}", "cyan")
        fields_conf = qsa_parser.parse_qsa_file(spec_path, project_prefix=q.project_prefix)
    elif file_ext in ('.yml', '.yaml'):
        # Parse YAML spec and build fields configuration
        cprint(f"Parsing YAML file: {spec_path}", "cyan")
        spec = _load_yaml(spec_path)
        fields_conf = _build_fields_conf(q, spec)
    else:
        raise ValueError(f"Unsupported file extension: {file_ext}. Use .yml, .yaml, or .qsa")

    # If dry-run, just print the YAML and exit
    if dry_run:
        cprint("\n=== Parsed YAML Configuration ===\n", "green")
        print(yaml.dump(fields_conf, default_flow_style=False, sort_keys=False))
        return

    # Bootstrap from baseline defined in config or overridden via --baseline/-b
    proj.bootstrap_project(q)

    # Note: Do NOT change process working directory; keep user shell unaffected

    # (Already handled above)

    # Write fields.yml
    fields_yml_path = q.join_path("fields.yml")
    with open(fields_yml_path, "w") as f:
        yaml.dump(fields_conf, f, sort_keys=False)
    cprint(f"Written fields.yml to {fields_yml_path}", "green")

    # Update template.json from fields
    q.update_fields()

    # Update code files from spec
    action_items = _ensure_action_items(fields_conf)
    _update_enums(q, action_items)
    _update_input_fields(q, fields_conf)
    _update_actions(q, action_items)
    _update_extension(q, action_items, fields_conf)

    cprint("Generation completed.", "green")


def _resolve_baseline_path(baseline: str) -> str:
    # Deprecated: baseline now comes from config or --baseline; keeping for backward compatibility
    if os.path.isabs(baseline) and os.path.isdir(baseline):
        return baseline
    if os.path.isdir(baseline):
        return baseline
    candidate = os.path.join(os.getcwd(), "baseline", baseline)
    return candidate


def _load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _slugify(name: str) -> str:
    s = str(name).strip().lower()
    s = re.sub(r"[\s/]+", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-+", "-", s)
    return s


def _build_fields_conf(q, spec: dict) -> dict:
    name = spec.get("name", q.template_name)
    description = spec.get("description", "")
    extension_name = q.extension_name
    var_prefix = (q.project_prefix or "ue")
    base = {
        "name": name,
        "template_type": "Extension",
        "agent_type": "Any",
        "extension": extension_name,
        "var_prefix": var_prefix,
        "description": description,
        "common_script": False,
        "always_cancel": False,
        "send_environment": "Launch",
        "send_variables": None,
    }

    fields = spec.get("fields", [])
    # ensure Action field exists
    has_action = any(list(f.keys())[0] == "action" for f in fields) if fields else False
    if not has_action:
        actions = spec.get("actions", ["run"])  # fallback single action
        fields.insert(0, {"action": "Choice", "items": actions, "required": True, "start": True})

    base["fields"] = fields
    base["events"] = spec.get("events", [])
    base["commands"] = spec.get("commands", [])
    return base


def _ensure_action_items(conf: dict):
    for f in conf.get("fields", []):
        name = list(f.keys())[0]
        if name == "action":
            items = f.get("items", [])
            # normalize to strings list
            result = []
            for it in items:
                if isinstance(it, str):
                    result.append(it)
                elif isinstance(it, dict):
                    result.append(list(it.keys())[0])
            return result
    return []


def _update_enums(q, actions):
    enums_path = q.join_path("src", "fields", "enums.py")
    os.makedirs(os.path.dirname(enums_path), exist_ok=True)
    with open(enums_path, "w") as f:
        f.write("from enum import Enum\n\n\n")
        f.write("class Action(Enum):\n")
        for act in actions:
            const = re.sub(r"[^A-Z0-9]", "_", act.upper())
            f.write(f"    {const} = \"{act}\"\n")


def _py_type(field_type: str) -> str:
    t = field_type.lower()
    if t in ("text", "large text", "large_text"):
        return "str"
    if t == "integer":
        return "int"
    if t == "float":
        return "float"
    if t == "boolean":
        return "bool"
    if t == "credential":
        return "Credential"
    if t == "array":
        return "list"
    if t == "choice":
        return "Action" if True else "str"
    return "str"


def _update_input_fields(q, fields_conf: dict):
    input_path = q.join_path("src", "fields", "input.py")
    os.makedirs(os.path.dirname(input_path), exist_ok=True)
    lines = []
    lines.append("from ue_commons.fields import InputFieldsModel")
    lines.append("from ue_commons.fields import Credential")
    lines.append("")
    lines.append("from fields.enums import Action")
    lines.append("")
    lines.append("")
    lines.append("class InputFields(InputFieldsModel):")

    for f in fields_conf.get("fields", []):
        name = list(f.keys())[0]
        ftype = list(f.values())[0]
        pytype = _py_type(ftype)
        default = f.get("default", None)
        if default is None:
            line = f"    {name}: {pytype}"
        else:
            if isinstance(default, str):
                dval = f'"{default}"'
            else:
                dval = str(default)
            line = f"    {name}: {pytype} = {dval}"
        lines.append(line)

    with open(input_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def _update_actions(q, actions):
    actions_path = q.join_path("src", "actions", "actions.py")
    os.makedirs(os.path.dirname(actions_path), exist_ok=True)
    existing = ""
    if os.path.exists(actions_path):
        with open(actions_path) as f:
            existing = f.read()

    header = (
        "from typing import Any, Dict\n"
        "from fields import InputFields\n\n"
    )

    blocks = []
    if not existing:
        blocks.append(header)

    for act in actions:
        func = act
        # Look for an existing function definition: def <func>(
        pattern = r"def\s+" + re.escape(func) + r"\s*\("
        if existing and re.search(pattern, existing):
            continue
        stub = (
            f"def {func}(input: InputFields) -> Dict[str, Any]:\n"
            f"    \"\"\"Auto-generated stub for action '{func}'.\"\"\"\n"
            f"    return {{'exit_code': 0, 'status_description': '{func} executed', 'json': {{}}}}\n\n"
        )
        blocks.append(stub)

    if blocks:
        mode = "a" if existing else "w"
        with open(actions_path, mode) as f:
            f.write("\n".join(blocks))


def _update_extension(q, actions, fields_conf):
    ext_path = q.join_path("src", "extension.py")
    os.makedirs(os.path.dirname(ext_path), exist_ok=True)
    body = []
    body.append("from typing import Any, Dict")
    body.append("")
    body.append("from ue_commons.core import ExtensionBase")
    body.append("from ue_commons.exceptions import exceptions_handler")
    body.append("from ue_commons.results import ExtensionJSONResult")
    body.append("from ue_commons.results import ExtensionResult")
    body.append("from ue_commons.decorators import dynamic_choice_command")
    body.append("")
    body.append("from fields import ExtensionOutput, InputFields, Invocation")
    body.append("from fields.enums import Action")
    body.append("from actions import actions as action_impl")
    body.append("")
    body.append("")
    body.append("class Extension(ExtensionBase):")
    body.append("    @exceptions_handler")
    body.append("    def extension_start(self, fields: dict) -> ExtensionJSONResult:")
    body.append("        input_fields = InputFields(**fields)")
    body.append("")
    body.append("        result = None")
    for idx, act in enumerate(actions):
        const = re.sub(r"[^A-Z0-9]", "_", act.upper())
        prefix = "if" if idx == 0 else "elif"
        body.append(f"        {prefix} input_fields.action == Action.{const}:")
        body.append(f"            result = action_impl.{act}(input_fields)")
    body.append("        else:")
    body.append("            raise ValueError(f\"Invalid action: {input_fields.action}\")")
    body.append("")
    body.append("        exit_code = result['exit_code']")
    body.append("        status_description = result['status_description']")
    body.append("        result_json = result['json']")
    body.append("        return create_extension_result(input_fields, result_json, exit_code=exit_code, status_description=status_description)")
    body.append("")
    body.append("    def extension_cancel(self):")
    body.append("        self.running = False")
    body.append("        self.log.warning('Extension cancelled!')")
    body.append("")
    # Dynamic choice handlers for fields with dynamic: true
    dynamic_fields = []
    for _f in fields_conf.get("fields", []):
        _name = list(_f.keys())[0]
        _dynamic = _f.get("dynamic", False)
        _type = str(list(_f.values())[0]).strip().lower()
        if _dynamic and _type in ("choice", "items", "select", "option", "options", "list"):
            dynamic_fields.append(_name)

    if dynamic_fields:
        body.append("    # Dynamic choice handlers")
        for _name in dynamic_fields:
            body.append(f"    @dynamic_choice_command(\"{_name}\")")
            body.append(f"    def get_{_name}(self, fields):")
            body.append("        _fields = []")
            body.append("        return ExtensionResult(")
            body.append("            rc=0,")
            body.append("            message=\"Available Fields: '{}'\".format(_fields),")
            body.append("            values=_fields")
            body.append("        )")
            body.append("")
    body.append("")
    body.append("def create_extension_result(")
    body.append("    input: InputFields,")
    body.append("    result: Dict[str, Any],")
    body.append("    exit_code: int = 0,")
    body.append("    status_description: str = 'Task executed successfully',")
    body.append(") -> ExtensionJSONResult:")
    body.append("    output = ExtensionOutput(")
    body.append("        exit_code=exit_code,")
    body.append("        status_description=status_description,")
    body.append("        invocation=Invocation(fields=input),")
    body.append("        result=result,")
    body.append("    )")
    body.append("")
    body.append("    return ExtensionJSONResult(")
    body.append("        output=output.dict(convert_to_null=True),")
    body.append("        exit_code=exit_code,")
    body.append("        message=status_description,")
    body.append("    )")

    with open(ext_path, "w") as f:
        f.write("\n".join(body) + "\n")
