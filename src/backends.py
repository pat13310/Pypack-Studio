from __future__ import annotations
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from PySide6 import QtCore

APP_ORG = "XenSoft"

@dataclass
class BuildConfig:
    project_dir: str = ""
    entry_script: str = ""
    name: str = "MyApp"
    icon_path: str = ""
    backend: str = "pyinstaller"  # "pyinstaller" | "nuitka"
    onefile: bool = True
    windowed: bool = True
    clean: bool = True
    console: bool = False
    add_data: List[Tuple[str, str]] = field(default_factory=list)  # (src, dst)
    directories_to_create: List[str] = field(default_factory=list)  # répertoires à créer dans le paquet
    hidden_imports: List[str] = field(default_factory=list)
    extra_args: List[str] = field(default_factory=list)
    output_dir: str = ""
    python_exe: str = ""  # optionnel : forcer un Python spécifique

    def validate(self) -> Tuple[bool, str]:
        if not self.entry_script:
            return False, "Le script d’entrée est requis."
        if not Path(self.entry_script).exists():
            return False, f"Script introuvable: {self.entry_script}"
        if not self.name:
            return False, "Le nom de l'application est requis."
        if self.icon_path and not Path(self.icon_path).exists():
            return False, f"Icône introuvable: {self.icon_path}"
        if self.backend not in {"pyinstaller", "nuitka"}:
            return False, f"Backend non supporté: {self.backend}"
        return True, ""

    def normalized(self) -> "BuildConfig":
        c = BuildConfig(**asdict(self))
        c.project_dir = normpath(c.project_dir or Path(self.entry_script).parent)
        c.entry_script = normpath(c.entry_script)
        c.icon_path = normpath(c.icon_path)
        c.output_dir = normpath(c.output_dir or str(Path(c.project_dir)/"dist"))
        c.python_exe = normpath(c.python_exe or detect_python_exe())
        c.add_data = [(normpath(a), b) for a, b in self.add_data]
        return c


def normpath(p: str | Path) -> str:
    if not p:
        return ""
    return str(Path(p).expanduser().resolve())


def detect_python_exe() -> str:
    return normpath(sys.executable)


def add_data_kv(pairs: List[Tuple[str, str]]) -> List[str]:
    """Convertit une liste (src, dst) en arguments --add-data compatibles PyInstaller.
    Sous Windows le séparateur est ';', sinon ':'
    """
    sep = ';' if os.name == 'nt' else ':'
    out = []
    for src, dst in pairs:
        if not src:
            continue
        srcp = normpath(src)
        if dst:
            out.append(f"{srcp}{sep}{dst}")
        else:
            out.append(f"{srcp}{sep}.")
    return out


class PackagerBackend(QtCore.QObject):
    def build_command(self, cfg: BuildConfig) -> List[str]:
        raise NotImplementedError

    def name(self) -> str:
        return "base"


class PyInstallerBackend(PackagerBackend):
    def name(self) -> str:
        return "pyinstaller"

    def build_command(self, cfg: BuildConfig) -> List[str]:
        # Base
        cmd = [cfg.python_exe, "-m", "PyInstaller"]
        if cfg.clean:
            cmd.append("--clean")
        cmd.extend(["--noconfirm", f"--name={cfg.name}"])
        if cfg.onefile:
            cmd.append("--onefile")
        if cfg.windowed and not cfg.console:
            cmd.append("--windowed")
        if cfg.icon_path:
            cmd.append(f"--icon={cfg.icon_path}")
        if cfg.output_dir:
            cmd.extend(["--distpath", cfg.output_dir])
        # add-data
        for pair in add_data_kv(cfg.add_data):
            cmd.extend(["--add-data", pair])
        # directories to create will be handled by creating placeholder files before build
        # hidden-imports
        for hi in cfg.hidden_imports:
            cmd.extend(["--hidden-import", hi])
        # extra
        cmd.extend(cfg.extra_args)
        # entry
        cmd.append(cfg.entry_script)
        return cmd


class NuitkaBackend(PackagerBackend):
    def name(self) -> str:
        return "nuitka"

    def build_command(self, cfg: BuildConfig) -> List[str]:
        # Nuitka: standalone pour embarquer l'interpréteur + deps
        cmd = [cfg.python_exe, "-m", "nuitka", "--standalone"]
        # --onefile reste optionnel sur Nuitka, plus lent mais pratique
        if cfg.onefile:
            cmd.append("--onefile")
        if cfg.windowed and not cfg.console:
            cmd.append("--windows-disable-console") if os.name == 'nt' else None
        if cfg.icon_path and os.name == 'nt':
            cmd.extend(["--windows-icon-from-ico", cfg.icon_path])
        if cfg.output_dir:
            cmd.extend(["--output-dir", cfg.output_dir])
        # data files
        for src, dst in cfg.add_data:
            # Nuitka utilise --include-data-file=SRC=DST (ou DATA-DIR)
            if src:
                dst_final = dst or os.path.basename(src)
                cmd.append(f"--include-data-file={src}={dst_final}")
        # directories to create will be handled by creating placeholder files before build
        # hidden imports
        for hi in cfg.hidden_imports:
            cmd.extend(["--include-module", hi])
        # nom
        if cfg.name:
            cmd.extend(["--product-name", cfg.name, "--company-name", APP_ORG])
            if os.name == 'nt':
                cmd.extend(["--file-version", "1.0.0", "--product-version", "1.0.0"])
        # extra
        cmd.extend(cfg.extra_args)
        # entry
        cmd.append(cfg.entry_script)
        return cmd


BACKENDS: Dict[str, PackagerBackend] = {
    "pyinstaller": PyInstallerBackend(),
    "nuitka": NuitkaBackend(),
}