import logging
from quip import cprint, yes_or_no, choose_one
import quip.external as external


def create_external_systems(q):
    repository_name = None
    gl_config = q._global_conf_external.get("gitlab", None)
    jnks_config = q._global_conf_external.get("jenkins", None)
    sq_config = q._global_conf_external.get("sonarqube", None)
    if gl_config is None:
        logging.warn("Gitlab configuration is missing in the uip_config file.")
    if jnks_config is None:
        logging.warn("Jenkins configuration is missing in the uip_config file.")
    if sq_config is None:
        logging.warn("SonarQube configuration is missing in the uip_config file.")

    if gl_config is not None:
        cprint("\n==== GITLAB SETUP ====", "blue")
        gl = initialize_gitlab(q, gl_config)
        setup_gitlab(q, gl, gl_config)
        repository_name = gl.repository_name

    if repository_name is None:
        # can not continue without repository_name
        logging.warn("Cannot continue without GitLab repository.")
        raise SystemExit(0)

    if jnks_config is not None:
        cprint("\n==== JENKINS SETUP ====", "blue")
        jnks = initialize_jenkins(q, jnks_config)

        gl_groups = gl_config.get("groups", [])
        jnks_groups = jnks_config.get("groups", {})
        jnks_group_details, jnks_repository_name = external.parse_repository_full_path(repository_name, gl_groups, jnks_groups)
        jnks_group_name = jenkins_credential = None
        if jnks_group_details:
            if isinstance(jnks_group_details, str):
                jnks_group_name = jnks_group_details
                jenkins_credential = "cs_prototype_api_personal_access_token"
            elif isinstance(jnks_group_details, dict):
                jnks_group_name = jnks_group_details["name"]
                jenkins_credential = jnks_group_details["credential"]
        setup_jenkins(q, jnks, jnks_group_name, jnks_repository_name, gl.base_url, repository_name, jenkins_credential)

    # create webhook for Jenkins
    if gl_config is not None and jnks_config is not None:
        jenkins_url = jnks.get_url(jnks_group_name, jnks_repository_name)
        if gl.create_webhook(jenkins_url):
            cprint("Webhook created", "green")
        if gl.create_badge(jenkins_url, jnks_config.get("url"), jnks_group_name, jnks_repository_name):
            cprint("Badge created", "green")

    if sq_config is not None:
        cprint("\n==== SONARQUBE SETUP ====", "blue")
        # check if SonarQube project exists
        sq_groups = sq_config.get("groups", {})
        if jnks_group_name in sq_groups:
            sq_group_name = sq_groups.get(jnks_group_name)
            if yes_or_no("Do you want to create SonarQube projects?", default=True):
                create_sonarqube(q, sq_group_name, jnks_repository_name, sq_config)
        else:
            cprint("No need to create SonarQube Project.", "green")


def setup_gitlab(q, gl, gl_config):
    repository_name = None

    import os
    git_path = template = q.join_path(".git", "config")
    if os.path.exists(git_path):
        repository_name = external.get_git_info(git_path, "origin")

    if repository_name is not None:
        cprint(f"Repository exists in git config: {repository_name}", "magenta")

        if check_gitlab_repository_exists(q, gl, repository_name):
            cprint(f"Repository exists in GitLab: {repository_name}", "green")
        else:
            cprint(f"Repository doesn't exist in GitLab: {repository_name}", "red")
            if yes_or_no("Do you want to create GitLab repository?", default=True):
                repository_name = create_gitlab(q, gl, repository_name, config=gl_config)
    else:
        if yes_or_no("Do you want to create Gitlab repository?", default=True):
            repository_name = create_gitlab(q, gl, config=gl_config)

    gl.repository_name = repository_name
    return gl


def setup_jenkins(q, jnks, jnks_group_name, jnks_repository_name, gitlab_url, repository_name, jenkins_credential):
    logging.debug(f"Group: {jnks_group_name}, Repository: {jnks_repository_name}")
    # Check if Jenkins Pipeline exists
    if jnks.check_job_exists(jnks_group_name, jnks_repository_name):
        cprint(f"Job exists in Jenkins: {jnks_group_name}/{jnks_repository_name}", "magenta")
    else:
        logging.info(f"Repository doesn't exist and will be created. {jnks_group_name}/{jnks_repository_name}")
        if yes_or_no("Do you want to create Jenkins Job?", default=True):
            jnks.create_job(jnks_group_name, jnks_repository_name, q.project_name, gitlab_url, repository_name, jenkins_credential)
            cprint(f"Jenkins job created: {jnks_group_name}/{jnks_repository_name}", "green")


def create_sonarqube(q, group_name, repository_name, sq_config):
    sq_url = sq_config.get("url", None)
    use_token = sq_config.get("use_token", True)
    if use_token:
        sq_pass = q.ask_password(sq_url, "token", prompt="Please enter Personal Access Key: ")
        username = sq_pass
        sq_pass = ""
    else:
        username = sq_config.get("username", None)
        if username is None:
            logging.error("Sonarqube username configuration is missing in the uip_config file.")
            return False

        sq_pass = q.ask_password(sq_url, username, prompt=f"Please enter SonarQube password for {username}: ")

    ssl_verify = sq_config.get("ssl_verify", True)
    sq = external.SonarQube(sq_url, (username, sq_pass), ssl_verify)
    prefix = group_name
    sq_project_name = prefix + "_" + repository_name
    sq.create_project(sq_project_name)


def create_gitlab(q, gl, repository_name=None, config=None):
    logging.info("Creating GitLab Repository.")

    if repository_name is None:
        groups = gl.get_groups()
        logging.debug(f"Groups = {groups}")
        group = choose_one(groups, title="Gitlab Groups", default=gl.default_group)
        logging.debug(f"Selected group = {group}")
        group_id = group[1]
        logging.debug(f"group_id = {group_id}")
        _group = gl.gl.groups.get(group_id)
        logging.debug(f"_group = {_group}")
        group_path = _group.full_path
        logging.debug(f"group_path = {group_path}")
        repository_name = f"{group_path}/{q.extension_name}"

    if check_gitlab_repository_exists(q, gl, repository_name):
        cprint(f"There is a repository already exists in GitLab. ({repository_name})", "yellow")
        cprint(f"Run `git remote add origin {gl.base_url}/{repository_name}.git", "yellow")
    else:
        gl.create_project(q.extension_name, group_id, config=config)
        cprint(f"Repository created {repository_name}", "green")

        if config.get("git-init", False):
            q.run_git("init")
            q.run_git(f"remote add origin {gl.base_url}/{repository_name}.git")
            if gl.default_branch is not None:
                import os
                if os.path.exists(q.join_path("README.md")):
                    os.rename(q.join_path("README.md"), q.join_path("README.md.temp"))
                q.run_git(f"checkout -b {gl.default_branch}")
                q.run_git(f"pull origin {gl.default_branch}")
                if os.path.exists(q.join_path("README.md.temp")):
                    os.remove(q.join_path("README.md"))
                    os.rename(q.join_path("README.md.temp"), q.join_path("README.md"))

        else:
            cprint(f"Run `git init`", "green")
            cprint(f"Run `git remote add origin {gl.base_url}/{repository_name}.git`", "green")

            if gl.default_branch is not None:
                cprint(
                    f"Default branch created. There will be an initial commit for that branch for README.md file",
                    "yellow",
                )
                cprint(f"Be sure you rename README.md file and run ", "yellow")
                cprint(f"     git checkout -b {gl.default_branch}", "yellow")
                cprint(f"     git pull origin {gl.default_branch}", "yellow")

    return repository_name


def check_gitlab_repository_exists(q, gl, repository_name):
    logging.info(f"Checking GitLab if the repository exists. Repository={repository_name}")

    projects = gl.get_projects()
    for project in projects:
        if repository_name == project[0]:
            gl.project_id = project[1]
            return True

    return False


def initialize_gitlab(q, gl_config):
    gl_url = gl_config.get("url", None)
    gl_token = q.ask_password(gl_url, "token", prompt="Please enter Personal Access Key: ")
    ssl_verify = gl_config.get("ssl_verify", True)
    default_group = gl_config.get("default_group", None)
    gl = external.GitLab(gl_url, gl_token, ssl_verify, default_group)
    return gl


def initialize_jenkins(q, jnks_config):
    logging.info("Connecting to Jenkins Server.")
    jnks_url = jnks_config.get("url", None)
    username = jnks_config.get("username", True)
    ssl_verify = jnks_config.get("ssl_verify", True)
    jnks_token = q.ask_password(jnks_url, username, prompt=f"Please enter Jenkins Password for ({username}): ")
    timeout = jnks_config.get("timeout", None)
    jnks = external.Jenkins(jnks_url, (username, jnks_token), ssl_verify=ssl_verify, timeout=timeout)
    return jnks


def create_jenkins(q, repository_name, jnks=None):
    logging.warning("create_jenkins is unused in refactor; keeping for parity.")
    if jnks is None:
        jnks_config = q._global_conf_external.get("gitlab", {})
        jnks_url = jnks_config.get("url", None)
        if jnks_url is None:
            logging.warn("Jenkins configuration is missing in the uip_config file.")
            return None

        username = jnks_config.get("username", True)
        jnks_token = q.ask_password(jnks_url, username, prompt=f"Please enter Jenkins Password for ({username}): ")
        ssl_verify = jnks_config.get("ssl_verify", True)
        default_group = jnks_config.get("default_group", None)
        timeout = jnks_config.get("timeout", None)
        jnks = external.Jenkins(
            jnks_url,
            (username, jnks_token),
            ssl_verify=ssl_verify,
            timeout=timeout,
        )
    projects = jnks.get_projects()
    for project in projects:
        if repository_name == project[0]:
            return True

    return False
