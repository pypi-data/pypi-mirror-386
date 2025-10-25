import logging
import os
import shutil

from distutils.dir_util import copy_tree
from quip import cprint, yes_or_no


def new_template(q):
    logging.info(f"creating new template {q.template_name}")
    if os.path.exists(q.project_folder_name):
        logging.error("Folder already exists")
        raise SystemExit(1)

    os.makedirs(q.project_folder_name)
    os.makedirs(q.join_path("src"))
    os.makedirs(q.join_path("src", "templates"))
    # Do not change working directory; leave shell location unchanged


def new_project(q):
    logging.info(f"creating new extension {q.template_name}")
    if os.path.exists(q.project_folder_name):
        print("ERROR: Folder already exists")
        raise SystemExit(1)

    os.makedirs(q.project_folder_name)
    q.uip_init(q.project_folder_name, q.default_template)
    q.update_extension_yaml(q.extension_name)
    q.update_uip_config(q.project_name, new_project=True)
    q.update_template_json(q.project_name, new_project=True)
    # Do not change working directory; leave shell location unchanged


def update_project(q, update_uuid=False, update_new_uuid=False, new_project=True):
    logging.debug(f"Updating extension {q.template_name}")
    if not q.args.template:
        q.update_extension_yaml(q.extension_name, new_project=new_project)
        q.update_uip_config(q.project_name, new_project=new_project)
    else:
        q.update_script_config(q.project_folder_name)
    q.update_template_json(q.project_name, update_uuid, update_new_uuid, new_project=new_project)


def clone_project(q, from_project_path, all_files=False, exclude_list=None):
    if not os.path.exists(from_project_path):
        logging.error(f"From path does NOT exists. {from_project_path}")
        raise SystemExit(1)

    from_project_src_path = os.path.join(from_project_path, "src")
    if not os.path.exists(from_project_src_path):
        logging.error("From path is not a extension path")
        raise SystemExit(1)

    if os.path.exists(q.project_folder_name):
        logging.error("Folder already exists")
        raise SystemExit(1)

    os.makedirs(q.project_folder_name)
    if not q.args.template:
        q.uip_init(q.project_folder_name, q.default_template)

    if not all_files:
        logging.debug("Copying all files to new folder.")
        files = copy_tree(from_project_src_path, q.join_path("src"))
    else:
        source_files = os.listdir(from_project_path)
        if exclude_list is not None:
            logging.debug(f"Ignoring following items: {exclude_list}")
            source_files = list(set(source_files) - set(exclude_list))
        for source_file in sorted(source_files):
            source_file_path = os.path.join(from_project_path, source_file)
            if os.path.isdir(source_file_path):
                files = copy_tree(source_file_path, q.join_path(source_file))
                for f in files:
                    logging.debug(f"Copying file {f}")
            else:
                shutil.copy2(source_file_path, q.join_path(source_file))
                logging.debug(f"Copying file {source_file}")

    q.update_project(update_uuid=True, update_new_uuid=True, new_project=True)


def bootstrap_project(q):
    # get bootstrap source
    if q.args.baseline:
        from_project_path = q.args.baseline
    else:
        from_project_path = q._global_conf_defaults.get("bootstrap", {}).get("source", None)
    if from_project_path is None:
        logging.error("Bootstrap source not found. Please check the config file.")
        raise SystemExit(2)

    exclude_list = q._global_conf_defaults.get("bootstrap", {}).get("exclude", None)

    clone_project(q, from_project_path, all_files=True, exclude_list=exclude_list)


def bootstrap_template(q, ask_for_upload=True):
    # get bootstrap source
    from_project_path = q._global_conf_defaults.get("bootstrap", {}).get("template_source", None)
    if from_project_path is None:
        logging.error("Bootstrap template source not found. Please check the config file.")
        raise SystemExit(2)

    exclude_list = q._global_conf_defaults.get("bootstrap", {}).get("template-exclude", None)

    clone_project(q, from_project_path, all_files=True, exclude_list=exclude_list)
    if ask_for_upload:
        answer = yes_or_no("Do you want to push the template to controller? ", default=True)
        if answer is True:
            q.upload_template()


def delete_project(q):
    logging.info(f"Deleting extension {q.template_name}")
    if not os.path.exists(q.project_folder_name):
        logging.error("Folder doesn't exist")
        raise SystemExit(1)

    shutil.rmtree(q.project_folder_name)


def delete_macos_hidden_files(q, dir_path):
    logging.debug(f"Deleting MacOS Hidden Files: {dir_path}")
    for filename in os.listdir(dir_path):
        if filename.startswith('.') or filename.startswith('._'):
            if filename == '.DS_Store' or filename == '.localized':
                os.remove(os.path.join(dir_path, filename))
            elif filename.startswith('._'):
                original_filename = filename[2:]
                original_file_path = os.path.join(dir_path, original_filename)
                if os.path.exists(original_file_path):
                    os.remove(os.path.join(dir_path, filename))
                else:
                    logging.debug(f"Skipping {filename} (corresponding original file not found)")
        elif os.path.isdir(os.path.join(dir_path, filename)):
            delete_macos_hidden_files(q, os.path.join(dir_path, filename))


def clean_project(q, full=True):
    import platform

    if full:
        folders = ["build", "dist", "temp", "downloads"]
    else:
        folders = ["build", "dist"]

    # Clean Mac specific files
    if platform.system() == 'Darwin':  # Check if the OS is macOS
        delete_macos_hidden_files(q, q.join_path("."))

    if not q.args.template:
        q.run_uip("clean")

    for folder in folders:
        folder_path = q.join_path(folder)

        if os.path.exists(folder_path):
            cprint(f"Deleting content of {folder_path}", color="blue")
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            try:
                shutil.rmtree(folder_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (folder_path, e))
