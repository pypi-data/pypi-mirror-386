__version__ = "1.0.4"
__modified__ = "2025-10-23"
__timestamp__ = "2025-10-23T20:29:21.181954+01:00"
__author__ = "LuxForge"
__status__ = "Production"

__changelog__ = [
    f"{__version__} - 2025-10-16: Added debug log messages to logger tests. Added README for logger.env. Updated logger env path to ./Logs.",
    f"{__version__} - 2025-10-18: Modified the name from luxforge-foundry to foundry for PyPI packaging.",
]

__audit_tags__ = [
    f"release:{__version__}",
    f"timestamp:{__timestamp__}",
    "packaging:twine",
    "build:python -m build",
    "push:rasputin_push.py",
]

import re

def update_pyproject_version(pyproject_path="pyproject.toml"):
    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_version = __version__

    updated = re.sub(
        r'(version\s*=\s*["\'])(.+?)(["\'])',
        lambda m: f'{m.group(1)}{new_version}{m.group(3)}',
        content,
        count=1
    )

    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"✔️ pyproject.toml updated to version {new_version}")