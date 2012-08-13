#!/usr/bin/env python2.7

"""Update a deployment of lp:linaro-license-protection.

This script assumes that initial deployment has been done in accordance
with the README as found in lp:linaro-license-protection/configs.

This means at least:

 * /srv/shared-branches/linaro-license-protection
   Branch of lp:linaro-license-protection (script will do 'bzr pull' on it)

 * /srv/shared-branches/linaro-license-protection-config
   Branch of lp:linaro-license-protection/configs

 * /srv/staging.snapshots.linaro.org/linaro-license-protection
   Checkout of /srv/shared-branches/linaro-license-protection
   (script will do an equivalent of 'bzr update' on it)

   Note that this applies to staging snapshots config.  Replace paths
   accordingly.

 * /srv/staging.snapshots.linaro.org/configs
   Checkout of /srv/shared-branches/linaro-license-protection-configs

 * /srv/staging.snapshots.linaro.org/db exists and is writeable by
   both apache and the user running update-deployment.py script.

 * /srv/staging.snapshots.linaro.org/linaro-license-protection/static
   is writeable by the user running update-deployment.py script.

Supported configs so far are snapshots.linaro.org, releases.linaro.org,
staging.snapshots.linaro.org and staging.releases.linaro.org.

"""

import argparse
import bzrlib.branch
import logging
import os
import subprocess

code_base = '/srv/shared-branches'
branch_name = 'linaro-license-protection'
configs_branch_name = 'linaro-license-protection-config'
snapshots_root = '/srv/snapshots.linaro.org'
releases_root = '/srv/releases.linaro.org'
staging_snapshots_root = '/srv/staging.snapshots.linaro.org'
staging_releases_root = '/srv/staging.releases.linaro.org'

configs_to_use = {
    "settings_releases": releases_root,
    "settings_snapshots": snapshots_root,
    "settings_staging_releases": staging_releases_root,
    "settings_staging_snapshots": staging_snapshots_root,
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


def update_installation(config, installation_root):
    """Updates a single installation code and databases.

    It expects code and config branches to be simple checkouts so it only
    does an "update" on them.

    Afterwards, it runs "syncdb" and "collectstatic" steps.
    """
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

    logger.debug("Doing 'collectstatic'...")
    logger.debug(subprocess.check_output(
        ["django-admin", "collectstatic", "--noinput"],
        cwd=code_root))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=(
            "Update staging deployment of lp:linaro-license-protection."))
    parser.add_argument(
        'configs', metavar='CONFIG', nargs='+', choices=configs_to_use.keys(),
        help=("Django configuration module to use. One of " +
              ', '.join(configs_to_use.keys())))
    parser.add_argument("-v", "--verbose", action='count',
                        help=("Increase the output verbosity. "
                              "Can be used multiple times"))
    args = parser.parse_args()

    if args.verbose == 0:
        logging_level = logging.ERROR
    elif args.verbose == 1:
        logging_level = logging.INFO
    elif args.verbose >= 2:
        logging_level = logging.DEBUG

    logger = logging.getLogger('update-staging')
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        level=logging_level)

    # Refresh code in shared-branches.
    refresh_branch(code_root)
    refresh_branch(configs_root)

    # We update installations for all the configs we've got.
    for config in args.configs:
        update_installation(config, configs_to_use[config])
