import logging
import os
import requests
import yaml

from quip import cprint, yes_or_no


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
