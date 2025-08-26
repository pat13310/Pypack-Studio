"""
Fichier contenant la classe BuildWorker pour l'application PyPack Studio.
"""

from PySide6 import QtCore
import shlex


class BuildWorker(QtCore.QObject):
    started = QtCore.Signal(list)
    line = QtCore.Signal(str)
    finished = QtCore.Signal(int)

    def __init__(self, cmd: list[str], workdir: str | None = None, env: dict[str, str] | None = None):
        super().__init__()
        self.cmd = cmd
        self.workdir = workdir
        self.env = env or {}
        self.proc = QtCore.QProcess()
        # Important: mode de canal pour récupérer stdout + stderr
        self.proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._on_ready)
        self.proc.finished.connect(self._on_finished)

    def start(self):
        self.started.emit(self.cmd)
        if self.workdir:
            self.proc.setWorkingDirectory(self.workdir)
        # Hériter l'environnement + ajouts
        env = QtCore.QProcessEnvironment.systemEnvironment()
        for k, v in (self.env or {}).items():
            env.insert(k, v)
        self.proc.setProcessEnvironment(env)
        # Lancer
        # Sous Windows, QProcess accepte une commande + liste d'arguments
        program = self.cmd[0]
        args = self.cmd[1:]
        self.proc.start(program, args)

    @QtCore.Slot()
    def _on_ready(self):
        data = self.proc.readAllStandardOutput()
        if data:
            try:
                text = bytes(data).decode(errors='replace')
            except Exception:
                text = str(data)
            for ln in text.splitlines():
                self.line.emit(ln)

    @QtCore.Slot(int, QtCore.QProcess.ExitStatus)
    def _on_finished(self, code: int, _status):
        self.finished.emit(code)

    def kill(self):
        if self.proc.state() != QtCore.QProcess.NotRunning:
            self.proc.kill()