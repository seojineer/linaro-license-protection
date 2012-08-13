#!/usr/bin/env python2.7

import bzrlib.branch
import logging


code_root = '/srv/shared-branches/linaro-license-protection'
configs_root = '/srv/shared-branches/linaro-license-protection-configs'

configs_to_use = [
    "settings_staging_releases",
    "settings_staging_snapshots",
    ]

logging_level = logging.DEBUG


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


if __name__ == '__main__':
    import os
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
        logger.info("Updating installation with config %s...", config)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", config)
        logger.debug("Doing 'syncdb'...")
        logger.debug(subprocess.check_output(
            ["python", "manage.py", "syncdb", "--noinput"], cwd=code_root))
        # At this time we could only be doing a single 'collectstatic' step,
        # but our configs might change.
        logger.debug("Doing 'collectstatic'...")
        logger.debug(subprocess.check_output(
            ["python", "manage.py", "collectstatic", "--noinput"],
            cwd=code_root))
