#!/usr/bin/env python3
# Author  : Huseyin Gomleksizoglu
# Date    : "26-May-2022"
# Version : quip.py: 20220526
#
# 1.0.0     Huseyin G.    Jun/2/2022    Icon feature added, build option added
#
# Copyright (c) Stonebranch Inc, 2019.  All rights reserved.


import argparse
import os, sys
import yaml
import shutil
import subprocess
import json
import uuid
import re
import logging
from distutils.dir_util import copy_tree
from getpass import getpass
import requests
from shutil import make_archive, unpack_archive, move
import tempfile
from datetime import datetime
import quip.field_builder as fb
import quip.version_builder as vb
import quip.external as external
from quip.fact import print_greeting
from argparse import RawTextHelpFormatter
from quip import __version__, yes_or_no, cprint, choose_one, color_text, is_quiet_mode, set_quiet_mode, resolve_quiet_mode, print_banner2, print_ascii_art2
from quip.services import icons_service as icons
from quip.services import fields_service as fields
from quip.services import template_service as tmpl
from quip.services import uip_service as uip
from quip.services import project_service as proj
from quip.services import external_service as ext
from quip.services import config_service as config_svc
from quip.services import version_service as ver
from quip.services import generator_service as generator
import keyring
import platform

version = __version__
UPDATE_ACTION = ["update", "u", "up"]
FIELD_ACTION = ["fields", "f", "fi"]
ICON_ACTION = ["icon", "resize-icon", "ri", "resize"]
DELETE_ACTION = ["delete", "d", "del"]
CLONE_ACTION = ["clone", "c", "cl", "copy"]
BOOTSTRAP_ACTION = ["bootstrap", "bs", "boot", "bst", "baseline"]
DOWNLOAD_ACTION = ["download", "pull"]
UPLOAD_ACTION = ["upload", "push"]
BUILD_ACTION = ["build", "b", "dist", "zip"]
CLEAN_ACTION = ["clean", "clear"]

class Quip:
    def __init__(self, log_level=logging.INFO) -> None:
        logging.basicConfig(level=log_level)
        self.in_project_folder = False
        self.args = self.parse_arguments()
        _cfg = getattr(self.args, 'config', None)
        if not isinstance(_cfg, (str, os.PathLike)):
            _cfg = None
        set_quiet_mode(resolve_quiet_mode(is_quiet_mode(), _cfg))
        action = getattr(self.args, 'action', None)
        if action in ("bootstrap", "setup"):
            print_ascii_art2()
        print_banner2(
            command=action,
            project=getattr(self.args, 'name', None),
            template=getattr(self.args, 'template', None),
            config=_cfg,
            quiet=is_quiet_mode(),
            debug=getattr(self.args, 'debug', None),
        )
        self.set_global_configs(self.args.name, _cfg)
        self.start_time = datetime.now()

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description='Wrapper for UIP command.', formatter_class=RawTextHelpFormatter)
        parser.add_argument('--version', action='version', version=f'quip {version}-BETA')
        # Common options available both before and after subcommands
        common = argparse.ArgumentParser(add_help=False)
        common.add_argument('--config', '-c', default=None,
                            help='path of the global config. Default is ~/.uip_config.yml')
        common.add_argument('--debug', '-v', action='store_true',
                            help='show debug logs')
        subparsers = parser.add_subparsers(dest='action')
        # Also add to root for convenience
        parser.add_argument('--config', '-c', default=None,
                             help='path of the global config. Default is ~/.uip_config.yml')
        parser.add_argument('--debug', '-v', action='store_true',
                            help='show debug logs')

        parser_new = subparsers.add_parser('new', parents=[common], help='Creates new integration')
        parser_new.add_argument('name', help='name of the project')
        parser_new.add_argument('--template', '-t', action='store_true',
                             help='create template instead of extension')

        parser_update = subparsers.add_parser('update', parents=[common], aliases=UPDATE_ACTION[1:], help='Updates existing integration')
        parser_update.add_argument('name', nargs="?", help='name of the project')
        parser_update.add_argument('--uuid', '-u', action='store_true',
                             help='Update UUID of the template')
        parser_update.add_argument('--new-uuid', '-n', action='store_true',
                             help='Update only new_uuid with a valid UUID in the template')
        parser_update.add_argument('--template', '-t', action='store_true',
                             help='create template instead of extension')
        parser_update.add_argument('--rename_scripts', action='store_true',
                             help='add .py extensions to script files.')
        
        parser_fields = subparsers.add_parser('fields', parents=[common], aliases=FIELD_ACTION[1:], help='Updates or dumps template.json fields.')
        parser_fields.add_argument('name', nargs="?", help='name of the project')
        parser_fields.add_argument('--update', '-u', action='store_true',
                             help='Update fields from fields.yml')
        parser_fields.add_argument('--dump', '-d', action='store_true',
                             help='dump fields to fields.yml')
        parser_fields.add_argument('--code', action='store_true',
                            help='Give some code samples')
        parser_fields.add_argument('--common', action='store_true',
                            help='Give some code samples in ue-common format')

        parser_delete = subparsers.add_parser('delete', parents=[common], aliases=DELETE_ACTION[1:], help='Deletes the integration folder')
        parser_delete.add_argument('name', help='name of the project')

        parser_clone = subparsers.add_parser('clone', parents=[common], aliases=CLONE_ACTION[1:], help='Clones existing integration with a new name')
        parser_clone.add_argument('name', help='name of the project')
        parser_clone.add_argument('source', help='source project path')
        parser_clone.add_argument('--template', '-t', action='store_true',
                             help='create template instead of extension')

        parser_bootstrap = subparsers.add_parser('bootstrap', parents=[common], aliases=BOOTSTRAP_ACTION[1:], help='Bootstrap new integration from baseline project')
        parser_bootstrap.add_argument('name', nargs="?", help='name of the project')
        parser_bootstrap.add_argument('--template', '-t', action='store_true',
                             help='create template instead of extension')
        parser_bootstrap.add_argument('--baseline', '-b',
                             help='Path of the baseline project')

        parser_upload = subparsers.add_parser('upload', parents=[common], aliases=UPLOAD_ACTION[1:], help='Uploads the template to Universal Controller. (Template Only)')
        parser_upload.add_argument('name', nargs="?", help='name of the project')
        parser_upload.add_argument('--template', '-t', action='store_true',
                             help='create template instead of extension')

        parser_download = subparsers.add_parser('download', parents=[common], aliases=DOWNLOAD_ACTION[1:], help='Download the template from Universal Controller.')
        parser_download.add_argument('name', nargs="?", help='name of the project')
        parser_download.add_argument('--template', '-t', action='store_true',
                             help='create template instead of extension')

        parser_build = subparsers.add_parser('build', parents=[common], aliases=BUILD_ACTION[1:], help='Builds a zip file to import to Universal Controller. (Template Only)')
        parser_build.add_argument('name', nargs="?", help='name of the project')
        parser_build.add_argument('--template', '-t', action='store_true',
                             help='create template instead of extension')

        parser_icon = subparsers.add_parser('icon', parents=[common], aliases=ICON_ACTION[1:], help='Resize the images to 48x48 in src/templates/')
        parser_icon.add_argument('name', nargs="?", help='name of the project')
        parser_icon.add_argument('--generate', '-g', metavar='TEXT', nargs='?', const=True,
                             help='generate new icon; optional TEXT (max 3 letters) to render')

        parser_clean = subparsers.add_parser('clean', parents=[common], aliases=CLEAN_ACTION[1:], help='Clears the dist folders')
        parser_clean.add_argument('name', nargs="?", help='name of the project')
        parser_clean.add_argument('--macfilesonly', '-m', action='store_true',
                             help='Delete only MacOS Hidden files like ._* or .DS_Store')

        parser_setup = subparsers.add_parser('setup', parents=[common], help='Setup External Systems')
        parser_setup.add_argument('name', nargs="?", help='name of the project')

        parser_setup = subparsers.add_parser('launch', parents=[common], help='Launch Task')
        parser_setup.add_argument('task_name', help='name of the task')

        parser_version = subparsers.add_parser('version', parents=[common], help='shows the version of the template/extension')
        parser_version.add_argument('version_method', nargs="?", choices=["minor", "major", "release", "beta", "rc"], help='update the version of the project. Options: beta,minor,major,release,rc.')
        parser_version.add_argument('--force', dest="forced_version", help='Force to change the version in all possible files')

        parser_config = subparsers.add_parser('config', parents=[common], help='show the configuration')

        parser_generate = subparsers.add_parser('generate', parents=[common], aliases=['gen', 'g'], help='Generate a new extension from spec (.yml/.yaml or .qsa); baseline from config or override with -b')
        parser_generate.add_argument('spec', help='Path to minimal spec file (.yml, .yaml, or .qsa)')
        parser_generate.add_argument('--baseline', '-b', help='Override baseline path. Defaults to config defaults.bootstrap.source')
        parser_generate.add_argument('--dry-run', '-d', action='store_true', help='Parse and print YAML output without creating project')

        args = parser.parse_args()
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)

        if args.action is None:
            parser.print_help()
            sys.exit(0)
        
        if args.action in ["config", "version", "launch"]:
            # give a fake name because name is mandatory
            args.name = ""
        
        # Resolve name and defaults for generate from spec file
        if args.action in ("generate", "gen", "g"):
            _, file_ext = os.path.splitext(args.spec)
            file_ext = file_ext.lower()

            if file_ext in ('.qsa',):
                # For QSA files, first line is the name
                try:
                    with open(args.spec, 'r', encoding='utf-8') as _f:
                        _nm = _f.readline().strip()
                except Exception as e:
                    logging.error(f"Failed to read QSA file {args.spec}: {e}")
                    sys.exit(2)
            elif file_ext in ('.yml', '.yaml'):
                # For YAML files, parse and extract name
                try:
                    with open(args.spec) as _f:
                        _spec_yaml = yaml.safe_load(_f) or {}
                except Exception as e:
                    logging.error(f"Failed to read spec file {args.spec}: {e}")
                    sys.exit(2)
                _nm = _spec_yaml.get("name")
            else:
                logging.error(f"Unsupported file extension: {file_ext}. Use .yml, .yaml, or .qsa")
                sys.exit(2)

            if not _nm or not isinstance(_nm, str):
                # fallback: derive from filename
                _nm = os.path.splitext(os.path.basename(args.spec))[0]
            args.name = _nm
        
        if args.action in (["clean"] + CLEAN_ACTION):
            # Ignore project name to clean macfiles
            if args.macfilesonly:
                args.name = ""

        if args.name is None:
            current_folder = os.getcwd()
            template_path = os.path.join(current_folder, "src", "templates", "template.json")
            if os.path.exists(template_path):
                # args.name = os.path.basename(current_folder)
                _json = self.read_template_json(template_path=template_path)
                template = (_json["templateType"] == "Script")
                if template:
                    args.name = "ut-" + _json["name"]
                    args.template = True
                else:
                    args.name = "ue-" + _json["name"]
                logging.debug(f"Project name: {args.name}")
                self.in_project_folder = True
            else:
                logging.error("You are not in a project folder. Please specify the project name.")
                sys.exit(1)

        if "template" not in dir(args):
            args.template = False
            logging.debug("No template keyword in args")
        elif args.template is False and args.name.startswith("ut-"):
            args.template = True
            logging.debug("Project is a template because name starts with UT")
        elif args.name.startswith("ue-"):
            args.template = False
            logging.debug("Project is an extension because name starts with UE")
        elif args.action in DOWNLOAD_ACTION and not self.in_project_folder:
            args.template = True
            logging.debug("Project is a template because download action executed with a name")
        
        logging.debug(f"The project is template={args.template}")
        return args
    
    def main(self):
        action = self.args.action
        if action == "new":
            if self.args.template:
                logging.info("creating new template")
                self.new_template()
            else:
                self.new_project()
                self.dump_fields(write=True)
            self.create_icon_safe()
        elif action in ICON_ACTION:
            if self.args.generate:
                msg = self.args.generate if isinstance(self.args.generate, str) else None
                self.create_icon(message=msg)
            else:
                self.update_icon()
        elif action in FIELD_ACTION:
            if self.args.dump:
                self.dump_fields(write=True)
            else:
                if self.args.common:
                    self.code_type = "common"
                self.update_fields(self.args.code)
        elif action in UPDATE_ACTION:
            if self.args.rename_scripts:
                self.update_rename_scripts()
            else:
                self.update_project(self.args.uuid, self.args.new_uuid, new_project=False)
            self.dump_fields(write=True)
        elif action in DELETE_ACTION:
            self.delete_project()
        elif action in CLONE_ACTION:
            if self.args.template:
                exclude_list = self._global_conf_defaults.get("bootstrap", {}).get("template-exclude", None)
            else:
                exclude_list = self._global_conf_defaults.get("bootstrap", {}).get("exclude", None)
            self.clone_project(self.args.source, all_files=True, exclude_list=exclude_list)
            self.dump_fields(write=True)
        elif action in ("generate", "gen", "g"):
            dry_run = getattr(self.args, 'dry_run', False)
            generator.generate(self, self.args.spec, dry_run=dry_run)
        elif action in BOOTSTRAP_ACTION:
            if self.args.template:
                self.bootstrap_template()
            else:
                self.bootstrap_project()
            self.dump_fields(write=True)
            self.create_icon_safe()
        elif action in UPLOAD_ACTION:
            self.update_fields_if_needed()
            if not self.args.template:
                self.run_uip("push_all")
            else:
                self.upload_template()
        elif action in DOWNLOAD_ACTION:
            if not self.args.template:
                self.run_uip("pull")
            else:
                if os.path.exists(self.project_folder_name) or self.in_project_folder:
                    self.download_template()
                else:
                    self.bootstrap_template(ask_for_upload=False)
                    self.download_template()
            self.dump_fields(write=True)
        elif action == "build":
            self.update_fields_if_needed()
            if self.args.template:
                self.build_zip(self.project_name)
            else:
                self.run_uip("build")
                self.curr_version = vb.find_current_version(version_files=self._version_files)
                if len(self.curr_version) == 1:
                    self.rename_build_package(self.curr_version[0])
        elif action == "config":
            if not self.uip_global_config.get("new", False):
                QuipGlobalConfig().check_config(self.uip_global_config)
            sys.exit(0)
        elif action == "setup":
            self.create_external_systems()
        elif action == "launch":
            self.launch_task()
        elif action in CLEAN_ACTION:
            if self.args.macfilesonly:
                self.delete_macos_hidden_files(".")
            else:
                self.clean_project()
            sys.exit(0)
        elif action == "version":
            self.curr_version = vb.find_current_version(version_files=self._version_files)
            if len(self.curr_version) == 0:
                logging.warning("There is no version information found.")
                cprint("There is no version information found.", color="red")
                sys.exit(1)
            
            self.show_version(self.curr_version, self.args.version_method)
            if self.args.version_method is not None:
                if len(self.curr_version) > 1:
                    logging.error("There are multiple versions. Fix that first.")
                    sys.exit(1)
                
                self.update_version(self.args.version_method, self.curr_version[0])
                self.clean_project(False)
            
            if self.args.forced_version is not None:
                if len(self.curr_version) > 1:
                    logging.warning(f"There are multiple versions but you forced to update them all to {self.args.forced_version}")
                
                for old_version in self.curr_version:
                    if old_version == self.args.forced_version:
                        continue
                    self.update_version("forced", old_version, self.args.forced_version)
                    self.clean_project(False)

    def set_global_configs(self, project_name, config_path=None):
        if config_path is not None:
            logging.debug(f"Using config from file : {config_path}")
        self.uip_global_config = config_svc.QuipGlobalConfig(config_file=config_path).conf
        logging.debug(self.uip_global_config)

        self._global_conf_defaults = self.uip_global_config.get("defaults", {})
        self._global_conf_extension = self.uip_global_config.get("extension.yml", {})
        self._global_conf_uip = self.uip_global_config.get("uip.yml", {})
        self._global_conf_external = self.uip_global_config.get("external", {})
        self._version_files = self.uip_global_config.get("version_files", None)
        self.default_template = self._global_conf_defaults.get("template", "ue-task")
        self.project_prefix = self._global_conf_defaults.get("project_prefix", None)
        # Removed: cd_on_create behavior (can't change parent shell cwd)
        self.project_name = self.format_ext_name(project_name)
        self.extension_name = self.project_folder_name = self.format_project_folder_name(project_name.lower(), self.args.template, self.project_prefix)
        self.template_name = self.titleize(project_name)
        self.use_keyring = self._global_conf_defaults.get("use_keyring", True)
        self.code_type = self._global_conf_defaults.get("code_type", "simple")
        logging.debug(f"Project Name: {self.project_name}")
        logging.debug(f"Template Name: {self.template_name}")
        logging.debug(f"Folder Name: {self.project_folder_name}")
        logging.debug(f"Code Type: {self.code_type}")

    def new_template(self):
        return proj.new_template(self)

    def new_project(self):
        return proj.new_project(self)

    def update_project(self, update_uuid=False, update_new_uuid=False, new_project=True):
        return proj.update_project(self, update_uuid=update_uuid, update_new_uuid=update_new_uuid, new_project=new_project)

    def update_rename_scripts(self):
        for _script in ["script", "scriptUnix", "scriptWindows"]:
            script_path = self.join_path("src", "templates", _script)
            if os.path.exists(script_path):
                os.rename(script_path, script_path + ".py")
                cprint(f"Script renamed: {script_path} => {script_path}.py", "yellow")

    def update_icon(self):
        return icons.update_icon(self)

    def create_icon_safe(self, message=None):
        return icons.create_icon_safe(self, message=message)

    def create_icon(self, message=None):
        return icons.create_icon(self, message=message)
    
    def get_icon_message(self, message):
        return icons.get_icon_message(self, message)

    def delete_project(self):
        return proj.delete_project(self)

    def delete_macos_hidden_files(self, dir_path):
        return proj.delete_macos_hidden_files(self, dir_path)

    def launch_task(self):
        self.run_uip("launch", self.args.task_name)

    def clean_project(self, full=True):
        return proj.clean_project(self, full=full)

    def clone_project(self, from_project_path, all_files=False, exclude_list=None):
        return proj.clone_project(self, from_project_path, all_files=all_files, exclude_list=exclude_list)

    def bootstrap_project(self):
        return proj.bootstrap_project(self)

    def bootstrap_template(self, ask_for_upload=True):
        return proj.bootstrap_template(self, ask_for_upload=ask_for_upload)

    def upload_template(self):
        zip_file_path = self.build_zip(self.project_name)

        uac_url = self._global_conf_uip.get("url", "http://localhost:8080/uc")
        uac_user = self._global_conf_uip.get("userid", "ops.admin")
        # uac_pass = input(f"Enter password for {uac_user}: ")
        uac_pass = self.ask_password(uac_url, uac_user)

        template_url = uac_url + "/resources/universaltemplate/importtemplate"
        logging.info(f"Uploading to controller ({uac_url})")
        with open(zip_file_path, "rb") as zipfile:
            zipfile_data = zipfile.read()
        result = requests.post(template_url, data=zipfile_data, auth=(uac_user, uac_pass), verify=False)
        if result.ok:
            logging.info(f"Template {self.template_name} pushed to {uac_url}")
        else:
            logging.error(f"Error while pushing {self.template_name} to {uac_url}")
            logging.error(f"Error detail: {result.text}")
            sys.exit(3)

    def upload_template_json(self):
        uac_user = self._global_conf_uip.get("userid", "ops.admin")
        uac_url = self._global_conf_uip.get("url", "http://localhost:8080/uc")
        template_url = uac_url + "/resources/universaltemplate"
        logging.info(f"Uploading to controller ({uac_url})")
        uac_pass = self.ask_password(uac_url, uac_user)
        payload = self.merge_template_scripts(self.project_name)
        logging.debug(f"Payload = {self.format_json(payload)}")
        
        answer = yes_or_no("Are you updating existing template? ", default=True)
        if answer == True:
            logging.info("Updating existing template")
            result = requests.put(template_url, json=payload, auth=(uac_user, uac_pass), verify=False)
        else:
            logging.info("Creating new template")
            result = requests.post(template_url, json=payload, auth=(uac_user, uac_pass), verify=False)
        
        if result.ok:
            logging.info(f"Template {self.template_name} pushed to {uac_url}")
        else:
            logging.error(f"Error while pushing {self.template_name} to {uac_url}")
            logging.error(f"Error detail: {result.text}")
            sys.exit(3)
        
        logging.info("Uploading icon")
        template_icon_url = uac_url + "/resources/universaltemplate/seticon?templatename=" + self.template_name
        # application/octet-stream, image/png
        headers = {"content-type": "image/png", "Accept": "plain/text"}
        with open(self.join_path("src", "templates", "template_icon.png"), "rb") as icon:
            icon_data = icon.read()
        icon_result = requests.post(template_icon_url, data=icon_data, auth=(uac_user, uac_pass), verify=False)
        
    def download_template(self, template_name=None):
        uac_user = self._global_conf_uip.get("userid", "ops.admin")
        uac_url = self._global_conf_uip.get("url", "http://localhost:8080/uc")
        logging.info(f"Downloading template from controller ({uac_url})")
        uac_pass = self.ask_password(uac_url, uac_user)

        if template_name is None:
            template_name = self.template_name

        #template_url = uac_url + "/resources/universaltemplate?templatename=" + self.template_name
        #headers = {"content-type": "application/json", "Accept": "application/json"}
        #logging.debug(f"Template URL is {template_url}")
        #result = requests.get(template_url, auth=(uac_user, uac_pass), headers=headers, verify=False)
        
        logging.info("Downloading template zip")
        template_url = uac_url + "/resources/universaltemplate/exporttemplate?templatename=" + self.template_name
        headers = {"Accept": "application/octet-stream"}
        logging.debug(f"Template URL is {template_url}")
        result = requests.get(template_url, auth=(uac_user, uac_pass), headers=headers, verify=False, allow_redirects=True)
        if result.ok:
            with tempfile.TemporaryDirectory() as tmpdirname:
                with open(os.path.join(tmpdirname, "template.zip"), "wb") as f:
                    f.write(result.content)
                download_folder = self.join_path("downloads")
                if not os.path.exists(download_folder):
                    os.makedirs(download_folder)
                shutil.copy2(os.path.join(tmpdirname, "template.zip"), os.path.join(download_folder, "template.zip"))
                logging.debug(f"Download file archived in download folder {download_folder}")
                logging.debug("Unpacking the zip file")
                unpack_archive(os.path.join(tmpdirname, "template.zip"), extract_dir=tmpdirname, format="zip")
                with open(os.path.join(tmpdirname, "template.json")) as json_f:
                    json_data = json_f.read()
                if os.path.exists(os.path.join(tmpdirname, "template_icon.png")):
                    logging.debug("Icon updated from zip file")
                    shutil.copy2(os.path.join(tmpdirname, "template_icon.png"), self.join_path("src", "templates", "template_icon.png"))
                else:
                    logging.warn("Icon file is missing")
            
            self.split_template_scripts(json.loads(json_data))
        else:
            logging.error(f"Error while downloading {self.template_name} from {uac_url}")
            logging.error(f"Error detail: {result.text}")
            sys.exit(3)

    def update_fields(self, code=False):
        return fields.update_fields(self, code=code)

    def update_fields_if_needed(self):
        return fields.update_fields_if_needed(self)

    def dump_fields(self, write=False):
        return fields.dump_fields(self, write=write)

    def create_external_systems(self):
        return ext.create_external_systems(self)
    
    def setup_gitlab(self, gl, gl_config):
        return ext.setup_gitlab(self, gl, gl_config)
    
    def setup_jenkins(self, *args, **kwargs):
        return ext.setup_jenkins(self, *args, **kwargs)

    def create_sonarqube(self, *args, **kwargs):
        return ext.create_sonarqube(self, *args, **kwargs)

    def create_gitlab(self, *args, **kwargs):
        return ext.create_gitlab(self, *args, **kwargs)
    
    def check_gitlab_repository_exists(self, gl, repository_name):
        return ext.check_gitlab_repository_exists(self, gl, repository_name)

    def initialize_gitlab(self, gl_config):
        return ext.initialize_gitlab(self, gl_config)

    
    def initialize_jenkins(self, jnks_config):
        return ext.initialize_jenkins(self, jnks_config)

    
    def create_jenkins(self, repository_name, jnks=None):
        return ext.create_jenkins(self, repository_name, jnks)

    def build_zip(self, project_name):
        return uip.build_zip(self, project_name)

    def show_version(self, current_versions, update):
        return ver.show_version(self, current_versions, update)

    def update_version(self, method, current_version, forced_version=None):
        return ver.update_version(self, method, current_version, forced_version)

    def titleize(self, name):
        if name[:3] in ["ue-", "ut-"]:
            name = name[3:]
        if name.lower() != name:
            # if name has uppercase than use it as-is
            return name
        name = name.replace("_", " ")
        name = name.replace("-", " ")
        name = name.replace("/", "")
        return name.title()

    def format_ext_name(self, name):
        name = name.replace("_", "-")
        name = name.replace(" ", "-")
        name = name.replace("/", "")
        name = name.replace("---", "-")
        name = name.replace("--", "-")
        return name.lower()
    
    def format_project_folder_name(self, project_name, template, prefix=None):
        if len(project_name) == 0:
            return project_name
        
        ext_name = self.format_ext_name(project_name.lower())

        if ext_name[:3] in ["ue-", "ut-"]:
            ext_name = ext_name[3:]
        
        if prefix is not None:
            if not ext_name.startswith(prefix):
                ext_name = prefix + "-" + ext_name

        if template:
            ext_name = "ut-" + ext_name
        else:
            ext_name = "ue-" + ext_name

        return ext_name

    def join_path(self, *paths):
        if self.in_project_folder:
            return os.path.join(os.getcwd(), *paths)
        else:
            return os.path.join(self.project_folder_name, *paths)

    def uip_init(self, project_name, default_template):
        # run uip init command
        command = f'''uip init -t {default_template} {project_name}'''
        logging.debug(f"Initializing the extension with command {command}")
        command = subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if command.returncode != 0:
            logging.error("UIP Init command failed.")
            logging.error(f"ERROR: Command is {command}")
            logging.error(f"ERROR: Return code is {command.returncode}")
            sys.exit(command.returncode)
    
    def run_uip(self, action, value=None):
        return uip.run_uip(self, action, value)
    
    def run_git(self, command):
        command = "git " + command
        cprint(command, color="yellow")
        result = subprocess.run(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        if result.returncode != 0:
            logging.error("GIT command failed.")
            logging.error(f"ERROR: Command is {command}")
            logging.error(f"ERROR: Return code is {command.returncode}")
            sys.exit(command.returncode)
        else:
            if len(result.stdout) > 0:
                cprint(f" GIT Output ".center(30, "="), color="yellow")
                for line in result.stdout.splitlines():
                    if line.lower().startswith("success"):
                        cprint(line, color="green")
                    elif line.lower().find("error") > 0:
                        cprint(line, color="red")
                    else:
                        print(line)
                cprint(f"=" * 30, color="yellow")
            
    def rename_build_package(self, version):
        return uip.rename_build_package(self, version)

    def update_extension_yaml(self, project_name, new_project=True):
        logging.debug("Updating extension.yml file")
        extension_config = self.join_path("src", "extension.yml")
        if os.path.exists(extension_config):
            if new_project:
                with open(extension_config, "w") as f:
                    _extension_config = self._global_conf_extension
                    _extension_config["extension"]["name"] = project_name
                    yaml.dump(_extension_config, f, sort_keys=False)
            else:
                with open(extension_config) as f:
                    _config = yaml.safe_load(f)

                with open(extension_config, "w") as f:
                    _config["extension"]["name"] = project_name
                    yaml.dump(_config, f, sort_keys=False)
            logging.debug("extension.yml file is updated")
        else:
            logging.error(f"ERROR: extension.yml file is missing! Path= {extension_config}")
            sys.exit(1)

    def update_uip_config(self, project_name, new_project=True):
        logging.debug("Updating uip.yml file")
        config = self.join_path(".uip", "config", "uip.yml")
        if os.path.exists(config):
            if new_project:
                with open(config, "w") as f:
                    _config = self._global_conf_uip
                    _config["template-name"] = self.template_name
                    yaml.dump(_config, f, sort_keys=False)
            else:
                with open(config) as f:
                    _config = yaml.safe_load(f)

                with open(config, "w") as f:
                    _config["template-name"] = self.template_name
                    yaml.dump(_config, f, sort_keys=False)
            logging.debug("uip.yml file is updated")
        else:
            logging.error(f"ERROR: uip.yml file is missing! Path= {config}")
            sys.exit(1)
    
    def update_script_config(self, project_name):
        logging.debug("Updating script.yml file")
        config = self.join_path("script.yml")
        
        if os.path.exists(config):
            with open(config) as f:
                _config = yaml.safe_load(f)

            with open(config, "w") as f:
                _config["script"]["name"] = project_name
                yaml.dump(_config, f, sort_keys=False)
                logging.debug("script.yml file is updated")
        else:
            logging.error(f"ERROR: script.yml file is missing! Path= {config}")
            sys.exit(1)

    def read_template_json(self, template_path):
        return tmpl.read_template_json(self, template_path)

    def update_template_json(self, project_name, update_uuid=False, update_new_uuid=False, new_project=False):
        return tmpl.update_template_json(self, project_name, update_uuid=update_uuid, update_new_uuid=update_new_uuid, new_project=new_project)
    
    def merge_template_scripts(self, project_name):
        return tmpl.merge_template_scripts(self, project_name)

    def split_template_scripts(self, payload_json):
        return tmpl.split_template_scripts(self, payload_json)
    
    def format_json(self, json_obj):
        json_string = json.dumps(json_obj, indent=4, sort_keys=True)
        json_string = re.sub(r"\n\s*\{", " {", json_string)
        json_string = re.sub(r"\n\s*\]", " ]", json_string)
        json_string = re.sub(r"\[\],", "[ ],", json_string)
        json_string = re.sub(r"\":(\s*[^\n]+)", "\" :\\1", json_string)
        return json_string

    def read_file_content(self, file_path):
        return tmpl.read_file_content(self, file_path)

    def write_to_file(self, file_path, content):
        return tmpl.write_to_file(self, file_path, content)

    def update_all_sysid_values(self, template_content):
        regex = re.compile(r"""\"sysId\"\s*:\s*\"([^\"]+)\"""")
        matches = regex.finditer(template_content)
        olds = set()
        for match in matches:
            old = match.group(1)
            if old in olds:
                continue

            new = self.get_new_uuid()
            logging.debug(f"Updating SysID: {old} => {new}")
            template_content = template_content.replace(old, new)
            olds.add(old)
        
        _json = json.loads(template_content)
        if "sysId" in _json:
            old = _json["sysId"]
            if not regex.match(old):
                new = self.get_new_uuid()
                logging.debug(f"Updating SysID: {old} => {new}")
                _json["sysId"] = new
                template_content = self.format_json(_json)
        
        return template_content

    def update_new_uuid_values(self, template_content):
        old = '"new_uuid"'
        for i in range(template_content.count(old)):
            new = "\"{}\"".format(self.get_new_uuid())
            logging.debug(f"Updating SysID: {old} => {new}")
            template_content = template_content.replace(old, new, 1)
        
        return template_content
    
    def get_new_uuid(self):
        return str(uuid.uuid4()).replace("-","")
    
    def ask_password(self, server, user_name, prompt=None, color='cyan', style='normal'):
        cprint(f"Server = `{server}`, User = `{user_name}`", color, style=style)
        quiet_mode = is_quiet_mode()
        saved_password = None

        if self.use_keyring:
            saved_password = keyring.get_password(server, user_name)

        if prompt is None:
            prompt = f'''Enter password for {user_name}: '''
            if self.use_keyring and saved_password is not None:
                prompt = f'''Enter password for {user_name} or [Enter] to use the existing password : '''
        else:
            if self.use_keyring and saved_password is not None:
                print("There is a saved password. To used the saved password just press [Enter]")

        if quiet_mode:
            logging.debug("Quiet mode enabled; attempting to reuse saved password for %s", user_name)
            password = ""
        else:
            if color is not None:
                prompt = color_text(prompt, color, style=style)
            password = getpass(prompt=prompt)

        if len(password) == 0:
            if self.use_keyring:
                if saved_password is not None:
                    logging.debug("Using password from Keyring")
                    password = saved_password
                else:
                    logging.error("Password is missing.")
                    return None
            else:
                logging.error("Password is missing.")
                return None
        else:
            if self.use_keyring:
                logging.debug("Updating the password in Keyring")
                keyring.set_password(server, user_name, password)

        return password

class QuipGlobalConfig:
    def __init__(self, config_file=None) -> None:
        self.conf = {}
        self.new_config = False
        if config_file is None:
            config_file = self.find_config_path()
        
        if config_file is not None:
            with open(config_file) as f:
                self.conf = yaml.safe_load(f)
            if self.new_config:
                self.conf["new"] = True

    def find_config_path(self, config_path=None):
        current_folder = os.path.curdir
        config_file = config_file_home = os.path.join(current_folder, ".uip_config.yml")
        if os.path.exists(config_file):
            logging.warning(f"Project specific config file found.")
        else:
            home_folder = os.path.expanduser("~")
            config_file = config_file_home = os.path.join(home_folder, ".uip_config.yml")
        
        if os.path.exists(config_file):
            logging.debug(f"Using config from file : {config_file}")
            return config_file
        else:
            logging.warn(f"Not using any config file. {config_file_home} or {config_file}")
            config_file = self.setup_config(config_file_home)
            self.new_config = True
            return config_file
    
    def setup_config(self, config_file):
        logging.info("You don't have any config file. I think this is the first time you are running this tool.")
        if yes_or_no(f"Do you want to download sample quip config? (Destination: {config_file}): ", default=True):
            response = requests.get("https://stb-se-dev.s3.amazonaws.com/quip/.uip_config.yml.sample")
            if response.ok:
                conf = yaml.safe_load(response.text)
                owner_name = input(f"Enter your name: ")
                conf["extension.yml"]["owner"]["name"] = owner_name

            with open(config_file, "w") as f:
                yaml.dump(conf, f, sort_keys=False)
            
            logging.info(f"Config file created. Check {config_file}")
            cprint("You need to pull the baseline projects. Use the following command.", color="cyan")
            cprint("git clone https://gitlab.stonebranch.com/cs-uac/ue-baseline.git", color="cyan")
            cprint("git clone https://gitlab.stonebranch.com/cs-uac/ut-baseline.git", color="cyan")
            
            self.check_config(conf)

            return config_file
        return None
    
    def check_config(self, conf):
        print(yaml.dump(conf, sort_keys=False))
        # check defaults
        if "defaults" not in conf:
            cprint("Defaults section is missing", color="red")
        else:
            if "template" not in conf["defaults"]:
                cprint("Defaults>template tag is missing", color="red")
            elif len(conf["defaults"]["template"]) == 0:
                cprint("Defaults>template value is empty.", color="red")
            
            if "bootstrap" not in conf["defaults"]:
                cprint("Defaults>bootstrap tag is missing", color="red")
            else:
                if "source" not in conf["defaults"]["bootstrap"]:
                    cprint("Defaults>bootstrap>source tag is missing", color="red")
                else:
                    if not os.path.exists(conf["defaults"]["bootstrap"]["source"]):
                        cprint("Defaults>bootstrap>source path is missing.", color="red")
                        cprint("Be sure you use full path of the ue-baseline project. You can clone the project by using the following command.", color="red")
                        cprint("git clone https://gitlab.stonebranch.com/integration-prototypes/ue-baseline.git\n", color="green")

                if "template_source" not in conf["defaults"]["bootstrap"]:
                    cprint("Defaults>bootstrap>template_source tag is missing", color="red")
                else:
                    if not os.path.exists(conf["defaults"]["bootstrap"]["template_source"]):
                        cprint("Defaults>bootstrap>template_source path is missing.", color="red")
                        cprint("Be sure you use full path of the ut-baseline project. You can clone the project by using the following command.", color="red")
                        cprint("git clone https://gitlab.stonebranch.com/integration-prototypes/ut-baseline.git\n", color="green")


class MyDumper(yaml.SafeDumper):
    # HACK: insert blank lines between top-level objects
    # inspired by https://stackoverflow.com/a/44284819/3786245
    def write_line_break(self, data=None):
        super().write_line_break(data)

        if len(self.indents) == 2:
            super().write_line_break()

def run():
    """Legacy entry point for backward compatibility."""
    _quip = Quip(log_level=logging.INFO)
    _quip.main()
    print_greeting(_quip)

def run_command(action, name, config_path, debug, **kwargs):
    """
    Bridge function to run commands from Click CLI.
    
    Args:
        action: Command action to perform
        name: Project name
        config_path: Path to config file
        debug: Debug mode flag
        **kwargs: Additional command-specific arguments
    """
    import sys
    from quip import is_quiet_mode
    
    # Build sys.argv to match old argparse format
    sys.argv = ['quip']
    
    if config_path:
        sys.argv.extend(['--config', config_path])
    if debug:
        sys.argv.append('--debug')
    
    # Add the action
    sys.argv.append(action)
    
    # Add the name if provided
    if name:
        sys.argv.append(name)
    
    # Add command-specific options
    if kwargs.get('template'):
        sys.argv.append('--template')
    if kwargs.get('uuid'):
        sys.argv.append('--uuid')
    if kwargs.get('new_uuid'):
        sys.argv.append('--new-uuid')
    if kwargs.get('rename_scripts'):
        sys.argv.append('--rename_scripts')
    if kwargs.get('update'):
        sys.argv.append('--update')
    if kwargs.get('dump'):
        sys.argv.append('--dump')
    if kwargs.get('code'):
        sys.argv.append('--code')
    if kwargs.get('common'):
        sys.argv.append('--common')
    if 'generate' in kwargs:
        gen = kwargs.get('generate')
        if isinstance(gen, str) and gen.strip():
            sys.argv.extend(['--generate', gen.strip()])
        elif gen:
            sys.argv.append('--generate')
    if kwargs.get('macfilesonly'):
        sys.argv.append('--macfilesonly')
    if kwargs.get('baseline'):
        sys.argv.extend(['--baseline', kwargs['baseline']])
    if kwargs.get('dry_run'):
        sys.argv.append('--dry-run')
    if kwargs.get('source'):
        sys.argv.append(kwargs['source'])
    if kwargs.get('spec'):
        sys.argv.append(kwargs['spec'])
    if kwargs.get('version_method'):
        sys.argv.append(kwargs['version_method'])
    if kwargs.get('forced_version'):
        sys.argv.extend(['--force', kwargs['forced_version']])
    
    # Run the command
    _quip = Quip(log_level=logging.DEBUG if debug else logging.INFO)
    _quip.main()
    print_greeting(_quip)

if __name__ == '__main__':
    _quip = Quip(log_level=logging.INFO)
    _quip.main()
    print_greeting(_quip)
