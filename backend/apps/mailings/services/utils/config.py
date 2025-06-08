import os
from django.conf import settings


def get_config_path(filename="Main.config"):
    """Return absolute path to the configuration file.

    The function looks for the file in the project root (one level above
    ``settings.BASE_DIR``) and inside ``settings.BASE_DIR``.
    ``settings.BASE_DIR`` points to ``backend/`` in this repository, but the
    configuration file might be placed in the repository root. If the file
    does not exist in either location, the path in the project root is
    returned so that callers can handle ``FileNotFoundError`` themselves."""
    # Potential locations
    project_root = os.path.abspath(os.path.join(settings.BASE_DIR, os.pardir))
    possible_paths = [
        os.path.join(project_root, filename),
        os.path.join(settings.BASE_DIR, filename),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    # Default: first path (project root)
    return possible_paths[0]
