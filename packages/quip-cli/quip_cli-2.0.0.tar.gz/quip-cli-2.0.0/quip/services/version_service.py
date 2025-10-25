import logging
from quip import cprint, yes_or_no
import quip.version_builder as vb


def show_version(q, current_versions, update):
    cprint(f"Current Version {current_versions}", color="green")
    if update is None:
        print(f"Possible next versions:")
        print(f"   RELEASE: ", vb.get_new_version("release", current_versions[0]))
        print(f"   MAJOR: ", vb.get_new_version("major", current_versions[0]))
        print(f"   MINOR: ", vb.get_new_version("minor", current_versions[0]))
        print(f"   BETA: ", vb.get_new_version("beta", current_versions[0]))
        print(f"   RC: ", vb.get_new_version("rc", current_versions[0]))


def update_version(q, method, current_version, forced_version=None):
    if forced_version is None:
        new_version = vb.get_new_version(method, q.curr_version[0])
    else:
        new_version = forced_version
    cprint(f"NEW Version will be {new_version}", color="green")
    answer = yes_or_no(
        f"Do you want to update the versions from {current_version} to {new_version}? ", default=True
    )
    if answer is True:
        vb.update_version(current_version, new_version, version_files=q._version_files)
