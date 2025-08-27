# src/services/file_manager.py
import shutil
from pathlib import Path
from typing import List

class FileManagerService:
    def __init__(self, log_service=None):
        self.log_service = log_service

    def copy_items(self, items: List[str], output_dir: str, app_name: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for path_str in items:
            src_path = Path(path_str)
            if not src_path.exists():
                self._log(f"Le chemin spécifié n'existe pas: {src_path}", "WARNING")
                continue

            try:
                if output_path.name == app_name:
                    app_output = output_path
                else:
                    app_output = output_path / app_name
                    app_output.mkdir(parents=True, exist_ok=True)

                if src_path.is_file() and src_path.suffix.lower() == ".png":
                    res_dir = app_output / "res"
                    res_dir.mkdir(parents=True, exist_ok=True)
                    dst_path = res_dir / src_path.name
                else:
                    dst_path = app_output / src_path.name

                if src_path.is_file():
                    shutil.copy2(src_path, dst_path)
                    self._log(f"Fichier copié: {src_path} -> {dst_path}", "INFO")
                else:
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    self._log(f"Répertoire copié: {src_path} -> {dst_path}", "INFO")

            except Exception as e:
                self._log(f"Erreur lors de la copie de {src_path}: {e}", "ERROR")

    def clean_output(self, output_dir: str):
        p = Path(output_dir)
        if not p.exists():
            self._log(f"{output_dir} n'existe pas.", "WARNING")
            return

        for child in p.iterdir():
            try:
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink(missing_ok=True)
            except Exception as e:
                self._log(f"Erreur suppression {child}: {e}", "ERROR")

        self._log(f"{output_dir} vidé.", "INFO")

    def _log(self, msg, level="INFO"):
        if self.log_service:
            self.log_service.append(msg, level)
