import hashlib
import inspect
from collections.abc import Iterable, Iterator, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import override

_CSS_MODULES: MutableMapping[Path, "CssModule"] = {}
_CSS_IMPORTS: dict[str, "CssImport"] = {}


def _caller_file() -> Path:
	frame = inspect.currentframe()
	try:
		if frame is None or frame.f_back is None:
			raise RuntimeError("Cannot determine caller frame for ps.css()")
		caller = frame.f_back
		# Walk past helper wrappers (ps.css may be imported under different name)
		while caller and caller.f_code.co_filename == __file__:
			caller = caller.f_back
		if caller is None:
			raise RuntimeError("Cannot determine caller for ps.css()")
		return Path(caller.f_code.co_filename).resolve()
	finally:
		del frame


def css_module(path: str | Path, *, relative: bool = False) -> "CssModule":
	source = Path(path)
	caller = _caller_file()
	if relative:
		source = caller.parent / source
	source = source.resolve()
	if not source.exists():
		raise FileNotFoundError(f"CSS module '{source}' not found")
	module = _CSS_MODULES.get(source)
	if not module:
		module = CssModule.create(source)
		_CSS_MODULES[source] = module
	return module


def css(path: str | Path, *, relative: bool = False) -> "CssImport":
	caller = _caller_file()
	if relative:
		source_path = (caller.parent / Path(path)).resolve()
		if not source_path.exists():
			raise FileNotFoundError(
				f"CSS import '{path}' not found relative to {caller.parent}"
			)
		key = f"file://{source_path}"
		existing = _CSS_IMPORTS.get(key)
		if existing:
			return existing
		imp = CssImport(
			_import_id(str(source_path)), specifier=None, source_path=source_path
		)
		_CSS_IMPORTS[key] = imp
		return imp

	spec = str(path)
	existing = _CSS_IMPORTS.get(spec)
	if existing:
		return existing
	imp = CssImport(_import_id(spec), specifier=spec, source_path=None)
	_CSS_IMPORTS[spec] = imp
	return imp


def registered_css_modules() -> list["CssModule"]:
	return list(_CSS_MODULES.values())


def registered_css_imports() -> list["CssImport"]:
	return list(_CSS_IMPORTS.values())


@dataclass(frozen=True)
class CssModule:
	id: str
	source_path: Path

	@staticmethod
	def create(path: Path) -> "CssModule":
		module_id = _module_id(path)
		return CssModule(module_id, path)

	def __getattr__(self, key: str) -> "CssReference":
		if key.startswith("__") and key.endswith("__"):
			raise AttributeError(key)
		return CssReference(self, key)

	def __getitem__(self, key: str) -> "CssReference":
		return self.__getattr__(key)

	def iter(self, names: Iterable[str]) -> Iterator["CssReference"]:
		for name in names:
			yield CssReference(self, name)


@dataclass(frozen=True)
class CssReference:
	module: CssModule
	name: str

	def __post_init__(self) -> None:
		if not self.name:
			raise ValueError("CSS class name cannot be empty")

	def __bool__(self) -> bool:
		raise TypeError("CssReference objects cannot be coerced to bool")

	def __int__(self) -> int:
		raise TypeError("CssReference objects cannot be converted to int")

	def __float__(self) -> float:
		raise TypeError("CssReference objects cannot be converted to float")

	@override
	def __str__(self) -> str:
		raise TypeError("CssReference objects cannot be converted to str")

	@override
	def __repr__(self) -> str:
		return f"CssReference(module={self.module.id!r}, name={self.name!r})"


def _module_id(path: Path) -> str:
	data = str(path).encode("utf-8")
	digest = hashlib.sha1(data).hexdigest()
	return f"css_{digest[:12]}"


@dataclass(frozen=True)
class CssImport:
	id: str
	specifier: str | None
	source_path: Path | None


def _import_id(value: str) -> str:
	data = value.encode("utf-8")
	digest = hashlib.sha1(data).hexdigest()
	return f"css_import_{digest[:12]}"


__all__ = [
	"CssModule",
	"CssReference",
	"CssImport",
	"css",
	"css_module",
	"registered_css_modules",
	"registered_css_imports",
]
