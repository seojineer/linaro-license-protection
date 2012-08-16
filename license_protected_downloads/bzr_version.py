# Copyright 2012 Linaro.
#
# Gets a bzr revision number for the directory this file lives in.
#

import bzrlib.branch
import os.path


def get_my_bzr_revno():
    """Returns a bzr revision number for the directory this file lives in."""
    branch_dir = os.path.join(os.path.dirname(__file__), '..')
    branch = bzrlib.branch.Branch.open(branch_dir)
    revision_info = branch.last_revision_info()
    return revision_info[0]
