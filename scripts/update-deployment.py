#!/usr/bin/env python

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

import os
import subprocess

from linaroscript import LinaroScript

code_base = '/srv/shared-branches'
branch_name = 'linaro-license-protection'
configs_branch_name = 'linaro-license-protection-configs'
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

code_root = os.path.join(code_base, branch_name)
configs_root = os.path.join(code_base, configs_branch_name)


class UpdateDeploymentScript(LinaroScript):

    def refresh_branch(self, branch_dir):
        """Refreshes a branch checked-out to a branch_dir."""
        self.run_subcommand(["bzr", "pull"], branch_dir)
        self.run_subcommand(["bzr", "up"], branch_dir)

    def run_subcommand(self, arguments, cwd=None):
        self.logger.debug("In %s, running: %s\n", cwd, str(arguments))
        process = subprocess.Popen(arguments, cwd=cwd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process_out, process_err = process.communicate()
        if process_out is not None:
            self.logger.debug(
                "stdout:\n" + "\n\t".join(process_out.splitlines()))
        if process_err is not None:
            self.logger.debug(
                "stderr:\n" + "\n\t".join(process_err.splitlines()))
        if process.returncode != 0:
            self.logger.error(
                "FAILED %d", process.returncode)

    def update_installation(self, config, installation_root):
        """Updates a single installation code and databases.

        It expects code and config branches to be simple checkouts
        (working trees) so it only does an "update" on them.

        Afterwards, it runs "syncdb" and "collectstatic" steps.
        """
        self.refresh_branch(os.path.join(installation_root, branch_name))
        self.refresh_branch(os.path.join(installation_root, "configs"))
        os.environ["PYTHONPATH"] = (
            ":".join(
                [installation_root,
                 os.path.join(installation_root, branch_name),
                 os.path.join(installation_root, "configs", "django"),
                 os.environ.get("PYTHONPATH", "")]))

        self.logger.info("Updating installation in %s with config %s...",
                         installation_root, config)
        os.environ["DJANGO_SETTINGS_MODULE"] = config
        self.logger.debug("DJANGO_SETTINGS_MODULE=%s",
                          os.environ.get("DJANGO_SETTINGS_MODULE"))

        self.logger.debug("Doing 'syncdb'...")
        self.run_subcommand(
                ["django-admin", "syncdb", "--noinput"], cwd=code_root)

        self.logger.debug("Doing 'collectstatic'...")
        self.run_subcommand(
                ["django-admin", "collectstatic", "--noinput"],
                cwd=code_root)

    def setup_parser(self):
        super(UpdateDeploymentScript, self).setup_parser()
        self.argument_parser.add_argument(
            '--bounce-apache', action='store_true', default=False,
            help="Whether to make Apache reload the configuration.")
        self.argument_parser.add_argument(
            'configs', metavar='CONFIG', nargs='+',
            choices=configs_to_use.keys(),
            help=("Django configuration module to use. One of " +
                  ', '.join(configs_to_use.keys())))

    def work(self):
        # Refresh code in shared-branches.
        self.refresh_branch(code_root)
        self.refresh_branch(configs_root)

        # We update installations for all the configs we've got.
        for config in self.arguments.configs:
            self.update_installation(config, configs_to_use[config])

        # Finally, bounce apache.
        if self.arguments.bounce_apache:
            self.run_subcommand(["sudo", "/etc/init.d/apache2", "reload"])


if __name__ == '__main__':
    script = UpdateDeploymentScript(
        'update-deployment',
        description=(
            "Update staging deployment of lp:linaro-license-protection."))
    script.run()
