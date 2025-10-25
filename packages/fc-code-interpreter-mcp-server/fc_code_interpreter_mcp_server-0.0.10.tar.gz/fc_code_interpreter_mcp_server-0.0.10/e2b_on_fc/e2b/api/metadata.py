import platform

from importlib import metadata

# Try to get e2b version, fallback to unknown
try:
    package_version = metadata.version("e2b")
except:
    package_version = "unknown"

default_headers = {
    "lang": "python",
    "lang_version": platform.python_version(),
    "machine": platform.machine(),
    "os": platform.platform(),
    "package_version": package_version,
    "processor": platform.processor(),
    "publisher": "e2b",
    "release": platform.release(),
    "sdk_runtime": "python",
    "system": platform.system(),
}
