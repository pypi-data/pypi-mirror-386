import json
import logging
import os
import re


def read_template_json(q, template_path):
    logging.debug("Reading template.json file")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            template_content = f.read()
            return json.loads(template_content)
    else:
        logging.error(f"ERROR: template.json file is missing! Path= {template_path}")
        raise SystemExit(1)


def update_template_json(q, project_name, update_uuid=False, update_new_uuid=False, new_project=False):
    logging.debug("Updating template.json file")
    template = q.join_path("src", "templates", "template.json")
    if os.path.exists(template):
        with open(template, "r") as f:
            template_content = f.read()
            if update_uuid:
                logging.debug("Updating SysIds in template.json")
                template_content = q.update_all_sysid_values(template_content)
            if update_new_uuid:
                logging.debug("Updating new_uuid with a valid SysIds in template.json")
                template_content = q.update_new_uuid_values(template_content)

        with open(template, "w") as f:
            _json = json.loads(template_content)
            if new_project:
                if "extension" in _json and _json["extension"] is not None:
                    _json["extension"] = q.extension_name
                _json["name"] = q.template_name
                if "variablePrefix" in _json:
                    if q.args.template:
                        _json["variablePrefix"] = "var"
                    else:
                        _json["variablePrefix"] = q.extension_name.replace("-", "_")
                        if len(_json["variablePrefix"]) > 20:
                            _json["variablePrefix"] = "ext"
            f.write(q.format_json(_json))
        logging.debug("template.json file is updated")
    else:
        logging.error(f"ERROR: template.json file is missing! Path= {template}")
        raise SystemExit(1)


def merge_template_scripts(q, project_name):
    logging.info("Merging scripts to template.json file")
    template = q.join_path("src", "templates", "template.json")
    if os.path.exists(template):
        with open(template, "r") as f:
            template_content = f.read()

        _json = json.loads(template_content)
        if _json["useCommonScript"]:
            script_path = q.join_path("src", "templates", "script.py")
            if not os.path.exists(script_path):
                script_path = q.join_path("src", "templates", "script")
            script_content = read_file_content(q, script_path)
            _json["script"] = r"""{}""".format(script_content)
            _json["scriptUnix"] = None
            _json["scriptWindows"] = None
        else:
            _json["script"] = None
            if _json["agentType"] in ["Linux/Unix", "Any"]:
                script_unix_path = q.join_path("src", "templates", "scriptUnix.py")
                if not os.path.exists(script_unix_path):
                    script_unix_path = q.join_path("src", "templates", "scriptUnix")
                script_unix_content = read_file_content(q, script_unix_path)
                _json["scriptUnix"] = script_unix_content

            if _json["agentType"] in ["Windows", "Any"]:
                script_windows_path = q.join_path("src", "templates", "scriptWindows.py")
                if not os.path.exists(script_windows_path):
                    script_windows_path = q.join_path("src", "templates", "scriptWindows")
                script_windows_content = read_file_content(q, script_windows_path)
                _json["scriptWindows"] = script_windows_content

        if "iconFilename" not in _json:
            icon_file = q.join_path("src", "templates", "template_icon.png")
            if os.path.exists(icon_file):
                logging.debug("Icon fields are added to the template.json payload.")
                _json["iconDateCreated"] = "2022-06-23 15:37:45"
                _json["iconFilename"] = "template_icon.png"
                _json["iconFilesize"] = os.path.getsize(icon_file)

        # Remove new fields to it can be imported to 7.1
        if "events" in _json:
            del _json["events"]
        if "sendVariables" in _json:
            del _json["sendVariables"]

        return _json
    else:
        logging.error(f"ERROR: template.json file is missing! Path= {template}")
        raise SystemExit(1)


def split_template_scripts(q, payload_json):
    if payload_json["useCommonScript"]:
        script_path = q.join_path("src", "templates", "script.py")
        write_to_file(q, script_path, payload_json["script"])
    else:
        if payload_json["agentType"] in ["Linux/Unix", "Any"]:
            script_unix_path = q.join_path("src", "templates", "scriptUnix.py")
            write_to_file(q, script_unix_path, payload_json["scriptUnix"])
        if payload_json["agentType"] in ["Windows", "Any"]:
            script_windows_path = q.join_path("src", "templates", "scriptWindows.py")
            write_to_file(q, script_windows_path, payload_json["scriptWindows"])

    payload_json["script"] = None
    payload_json["scriptUnix"] = None
    payload_json["scriptWindows"] = None

    # Remove new fields to it can be imported to 7.1
    if "events" in payload_json:
        del payload_json["events"]
    if "sendVariables" in payload_json:
        del payload_json["sendVariables"]

    template = q.join_path("src", "templates", "template.json")
    with open(template, "w") as f:
        f.write(q.format_json(payload_json))
        logging.debug("template.json file is updated")


def read_file_content(q, file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
    else:
        logging.error(f"ERROR: file is missing! Path= {file_path}")
        raise SystemExit(1)

    return content


def write_to_file(q, file_path, content):
    try:
        short_file_path = file_path.replace(os.getcwd(), "")
        if content is None:
            logging.warn(f"Script Content for {short_file_path} is empty.")
            return

        if os.path.exists(file_path):
            from quip import yes_or_no

            if not yes_or_no(
                f"Do you want to overwrite the script file? ({short_file_path}): ", default=False
            ):
                logging.info("Script file NOT updated.")
                return None

        logging.info(f"Script file updated: {short_file_path}")
        with open(file_path, "w") as f:
            f.write(content)
    except Exception as ex:
        logging.error(f"ERROR: While writing to file! Path= {file_path}")
        logging.error(f"ERROR: {ex}")
        raise SystemExit(1)
