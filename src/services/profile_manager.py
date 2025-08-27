# src/services/profile_manager.py
import json
from dataclasses import asdict
from typing import Dict
from PySide6.QtCore import QSettings

class ProfileManager:
    def __init__(self, settings: QSettings, key: str = "profiles"):
        self.settings = settings
        self.key = key

    def load_all(self) -> Dict[str, dict]:
        raw = self.settings.value(self.key, "{}")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def save_all(self, data: Dict[str, dict]):
        self.settings.setValue(self.key, json.dumps(data, ensure_ascii=False, indent=2))

    def get(self, name: str) -> dict | None:
        return self.load_all().get(name)

    def save(self, name: str, cfg):
        """Sauvegarde un profil à partir d'un BuildConfig ou dict"""
        data = self.load_all()
        data[name] = asdict(cfg) if not isinstance(cfg, dict) else cfg
        self.save_all(data)

    def delete(self, name: str):
        data = self.load_all()
        if name in data:
            del data[name]
            self.save_all(data)

    def export_to_file(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.load_all(), f, ensure_ascii=False, indent=2)

    def import_from_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Format invalide")
        self.save_all(data)
