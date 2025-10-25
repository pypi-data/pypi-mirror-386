import logging
import os
import subprocess
from shutil import make_archive, move
import tempfile

import yaml

from . import template_service as tmpl
from quip import cprint


def run_uip(q, action, value=None):
    need_pass = False
    uac_url = q._global_conf_uip["url"]
    uac_user = q._global_conf_uip["userid"]
    if action in ["push_all", "push"]:
        additional_params = "-a" if action == "push_all" else ""
        command = f"""uip push {additional_params} -i {uac_url} -u {uac_user}"""
        need_pass = True
    elif action == "pull":
        need_pass = True
        command = f"""uip pull -i {uac_url} -u {uac_user}"""
    elif action == "build":
        need_pass = False
        command = f"""uip build -a"""
    elif action == "clean":
        need_pass = False
        command = f"""uip clean"""
    elif action == "launch":
        need_pass = True
        command = f"""uip task launch "{value}" -i {uac_url} -u {uac_user}"""
    else:
        raise ValueError(f"Unknown UIP action: {action}")

    if need_pass:
        uac_pass = q.ask_password(uac_url, uac_user)
        os.environ["UIP_PASSWORD"] = uac_pass

    logging.debug(f"Initializing the extension with command {command}")
    cprint(command, color="yellow")

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )

    output_lines = []
    header_printed = False

    try:
        if process.stdout:
            for raw_line in process.stdout:
                line = raw_line.rstrip("\n")
                output_lines.append(line)

                if not header_printed:
                    cprint(f" UIP Output ".center(30, "="), color="yellow")
                    header_printed = True

                lower_line = line.lower()
                if lower_line.startswith("success"):
                    cprint(line, color="green")
                elif "error" in lower_line:
                    cprint(line, color="red")
                else:
                    print(line)
    finally:
        if process.stdout:
            process.stdout.close()

    return_code = process.wait()

    if return_code != 0:
        logging.error("UIP command failed.")
        logging.error(f"ERROR: Command is {command}")
        logging.error(f"ERROR: Return code is {return_code}")
        if output_lines:
            for line in output_lines:
                logging.error(line)
        raise SystemExit(return_code)
    else:
        if header_printed:
            cprint("=" * 30, color="yellow")


def build_zip(q, project_name):
    import os
    import shutil
    from datetime import datetime

    with tempfile.TemporaryDirectory() as tmpdirname:
        logging.debug(f"Created temporary directory {tmpdirname}")
        payload = tmpl.merge_template_scripts(q, q.project_name)
        template = os.path.join(tmpdirname, "template.json")
        with open(template, "w") as f:
            f.write(q.format_json(payload))
        template_icon = q.join_path("src", "templates", "template_icon.png")
        shutil.copy2(template_icon, os.path.join(tmpdirname, "template_icon.png"))
        if os.path.exists("script.yml"):
            with open("script.yml") as f:
                conf = yaml.safe_load(f)
                version = conf.get("script", []).get("version")
        else:
            version = datetime.now().strftime("%Y%m%d")

        archive_name = f"unv-tmplt-{q.format_ext_name(project_name.lower())}-{version}"
        new_archive_file = make_archive(archive_name, "zip", root_dir=tmpdirname)
        logging.info(f"Archive file created. File name is {archive_name}.zip")
        build_folder = q.join_path("build")
        if not os.path.exists(build_folder):
            os.makedirs(build_folder)
        move(new_archive_file, os.path.join(build_folder, archive_name + ".zip"))
        logging.debug(f"Archive file {archive_name}.zip moved to {build_folder}")
    return os.path.join(build_folder, archive_name + ".zip")


def rename_build_package(q, version):
    import os
    import shutil

    package_folder = q.join_path("dist", "package_build")
    for filename in os.listdir(package_folder):
        if filename.endswith("universal_template.zip"):
            base_filename = "unv-tmplt-" + os.path.basename(filename).replace(
                "_universal_template.zip", f"-{version}.zip"
            ).replace("_", " ")
            new_filename = os.path.join(os.path.dirname(filename), base_filename)
            new_filepath = q.join_path("dist", "package_build", new_filename)
            if os.path.exists(new_filepath):
                shutil.move(q.join_path("dist", "package_build", filename), new_filepath)
            else:
                os.rename(q.join_path("dist", "package_build", filename), new_filepath)
            cprint(f"File Renamed: {filename} => {new_filename}", "yellow")
