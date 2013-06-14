import os

def safe_path_join(base_path, *paths):
    """os.path.join with check that result is inside base_path.

    Checks that the generated path doesn't end up outside the target
    directory, so server accesses stay where we expect them.
    """

    target_path = os.path.join(base_path, *paths)

    if not target_path.startswith(base_path):
        return None

    if not os.path.normpath(target_path) == target_path.rstrip("/"):
        return None

    return target_path
