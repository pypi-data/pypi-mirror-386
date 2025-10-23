"""
Pulse package version indicator.

This module exposes `__version__` which is guaranteed to match the
distribution version declared in `pyproject.toml` when installed.

During editable/development usage (when importlib.metadata cannot find the
installed distribution), we fall back to reading the nearby `pyproject.toml`
to keep version information consistent without duplication.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

__all__ = ["__version__"]


def _read_local_pyproject_version() -> str | None:
	"""Best-effort read of version from a local pyproject.toml (dev/editable).

	Searches upwards from this file to find `packages/pulse/python/pyproject.toml` and
	parses the minimal `version = "x.y.z"` line without importing tomllib to
	avoid unnecessary dependency at runtime.
	"""

	try:
		here = Path(__file__).resolve()
		root = (
			here.parent.parent.parent
		)  # packages/pulse/python/src/pulse -> packages/pulse/python
		pyproject = root / "pyproject.toml"
		if not pyproject.exists():
			return None
		for line in pyproject.read_text().splitlines():
			line = line.strip()
			if line.startswith("version") and "=" in line:
				# naive parse: version = "0.0.0"
				try:
					_, rhs = line.split("=", 1)
					rhs = rhs.strip().strip("\"'")
					if rhs:
						return rhs
				except Exception:
					return None
		return None
	except Exception:
		return None


def _version() -> str:
	# Primary: installed distribution metadata
	try:
		return _pkg_version("pulse-framework")
	except PackageNotFoundError:
		pass

	# Fallback: local pyproject during dev/editable installs
	local = _read_local_pyproject_version()
	if local:
		return local

	# Last resort to avoid exceptions (should not happen in practice)
	return "0.0.0"


__version__: str = _version()
