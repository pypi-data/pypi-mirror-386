# src/agents_boot/channels/pypi.py
from __future__ import annotations
import os, subprocess, shlex, pathlib
from .base import ChannelAdapter, Product, PublishResult

class PyPIChannel(ChannelAdapter):
    """
    Builds and uploads with 'python -m build' and 'twine upload'.
    Requires env:
      - TWINE_USERNAME
      - TWINE_PASSWORD  (or use token with __token__)
    Config keys:
      - project_root: str (default ".")
      - repository_url: Optional[str] # e.g. https://upload.pypi.org/legacy/ or testpypi
    """
    name = "pypi"

    def publish(self, p: Product) -> PublishResult:
        proj = pathlib.Path(self.config.get("project_root", "."))
        dist = proj / "dist"
        if dist.exists():
            for f in dist.glob("*"):
                f.unlink()  # clean
        subprocess.run([shlex.split("python -m build")][0], check=True, cwd=str(proj))
        cmd = "python -m twine upload dist/*"
        if self.config.get("repository_url"):
            cmd += f" --repository-url {self.config['repository_url']}"
        subprocess.run(shlex.split(cmd), check=True, cwd=str(proj))
        return PublishResult(channel=self.name)
