#!/usr/bin/env python2.7

import bzrlib.branch
import logging
import os

code_base = '/srv/shared-branches'
branch_name = 'linaro-license-protection'
configs_branch_name = 'linaro-license-protection-config'
snapshots_root = '/srv/staging.snapshots.linaro.org'
releases_root = '/srv/staging.releases.linaro.org'

configs_to_use = {
    "settings_staging_releases": releases_root,
    "settings_staging_snapshots": snapshots_root,
    }

logging_level = logging.DEBUG

code_root = os.path.join(code_base, branch_name)
configs_root = os.path.join(code_base, configs_branch_name)


def refresh_branch(branch_dir):
    """Refreshes a branch checked-out to a branch_dir."""

    code_branch = bzrlib.branch.Branch.open(branch_dir)
    parent_branch = bzrlib.branch.Branch.open(
        code_branch.get_parent())
    result = code_branch.pull(source=parent_branch)
    if result.old_revno != result.new_revno:
        logger.info("Updated %s from %d to %d.",
                    branch_dir, result.old_revno, result.new_revno)
    else:
        logger.info("No changes to pull from %s.", code_branch.get_parent())
    return code_branch


def update_branch(branch_dir):
    """Does a checkout update."""
    code_branch = bzrlib.branch.Branch.open(branch_dir)
    code_branch.update()


if __name__ == '__main__':
    import subprocess

    logger = logging.getLogger('update-staging')
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        level=logging_level)

    # Refresh code.
    refresh_branch(code_root)
    refresh_branch(configs_root)

    # For all configs we've got, do a 'syncdb' and 'collectstatic' steps.
    for config in configs_to_use:
        installation_root = configs_to_use[config]
        update_branch(os.path.join(installation_root, branch_name))
        update_branch(os.path.join(installation_root, "configs"))
        os.environ["PYTHONPATH"] = (
            ":".join(
                [installation_root,
                 os.path.join(installation_root, branch_name),
                 os.path.join(installation_root, "configs", "django"),
                 os.environ.get("PYTHONPATH", "")]))

        logger.info("Updating installation in %s with config %s...",
                    installation_root, config)
        os.environ["DJANGO_SETTINGS_MODULE"] = config
        logger.debug("DJANGO_SETTINGS_MODULE=%s",
                     os.environ.get("DJANGO_SETTINGS_MODULE"))
        logger.debug("Doing 'syncdb'...")
        logger.debug(subprocess.check_output(
            ["django-admin", "syncdb", "--noinput"], cwd=code_root))
        # At this time we could only be doing a single 'collectstatic' step,
        # but our configs might change.
        logger.debug("Doing 'collectstatic'...")
        logger.debug(subprocess.check_output(
            ["django-admin", "collectstatic", "--noinput"],
            cwd=code_root))
