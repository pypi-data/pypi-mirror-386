import json
import logging
import os
import yaml

import quip.field_builder as fb
from .config_service import MyDumper
from quip import yes_or_no, cprint


def update_fields(q, code=False):
    fields_path = q.join_path("fields.yml")
    if os.path.exists(fields_path):
        with open(fields_path) as f:
            conf = yaml.safe_load(f)
            template_dict = fb.prepare_template_fields(conf)
            new_fields = conf.get("fields", [])

            logging.debug("FIELDS: %s", new_fields)
            fields_dict = fb.prepare_fields(new_fields, code, code_type=q.code_type)
            template_dict["fields"] = fields_dict

            new_events = conf.get("events", [])
            logging.debug("EVENTS: %s", new_events)
            events_dict = fb.prepare_event_fields(new_events)
            template_dict["events"] = events_dict

            new_commands = conf.get("commands", [])
            logging.debug("commands: %s", new_commands)
            commands_dict = fb.prepare_command_fields(new_commands, fields_dict)
            template_dict["commands"] = commands_dict

        logging.debug("Updating template.json file")
        template = q.join_path("src", "templates", "template.json")
        if os.path.exists(template):
            with open(template, "r") as f:
                template_content = f.read()

            _json = json.loads(template_content)
            _json.update(template_dict)

            with open(template, "w") as f:
                f.write(q.format_json(_json))
                logging.debug("template.json file is updated")
            dump_fields(q, write=True)
            logging.debug("fields.yml updated")

            # have modified time of template be later than fields.yml
            os.utime(template)
        else:
            logging.error(f"ERROR: template.json file is missing! Path= {template}")
            raise SystemExit(1)
    else:
        logging.error("fields.yml file is missing")
        raise SystemExit(4)


def update_fields_if_needed(q):
    template_json_path = q.join_path("src", "templates", "template.json")
    fields_path = q.join_path("fields.yml")
    if os.path.getmtime(fields_path) > os.path.getmtime(template_json_path):
        cprint("It looks like fields.yml file changed.", "cyan")
        if yes_or_no("Do you want to update template.json?", default=True, color="cyan"):
            update_fields(q)


def dump_fields(q, write=False):
    logging.debug("Writing fields to fields.yml file")
    template = q.join_path("src", "templates", "template.json")
    if os.path.exists(template):
        with open(template, "r") as f:
            template_content = f.read()
            _json = json.loads(template_content)
            template_dict = fb.dump_template_fields(_json)
            fields_dict = fb.dump_fields(_json.get("fields"))
            template_dict["fields"] = fields_dict
            events_dict = fb.dump_events(_json.get("events", None))
            template_dict["events"] = events_dict
            commands_dict = fb.dump_commands(_json.get("commands", None), _json.get("fields"))
            template_dict["commands"] = commands_dict
            yaml_dump = yaml.dump(template_dict, Dumper=MyDumper, default_flow_style=False, sort_keys=False, width=1000)
            yaml_dump = yaml_dump.replace('fields:\n', '\nfields:')
            yaml_dump = yaml_dump.replace('events:\n', '\nevents:')
            yaml_dump = yaml_dump.replace('commands:\n', '\ncommands:')
            if not write:
                print(yaml_dump)
            else:
                fields_path = q.join_path("fields.yml")
                with open(fields_path, "w") as f2:
                    f2.write(yaml_dump)

        # Update template.json time
        os.utime(template)
    else:
        logging.error(f"ERROR: template.json file is missing! Path= {template}")
        raise SystemExit(1)
