# src/agents_boot/channels/dockerhub.py
from __future__ import annotations
import os, subprocess, shlex
from typing import Dict, Any
from .base import ChannelAdapter, Product, PublishResult

class DockerHubChannel(ChannelAdapter):
    """
    Uses shell commands you provide to build & push.
    Config keys (examples):
      - build_cmd: "docker build -t ORG/REPO:TAG ."
      - push_cmd: "docker push ORG/REPO:TAG"
      - image_url: "https://hub.docker.com/r/ORG/REPO"
    If you already have p.artifacts['docker_image'], we skip build_cmd and just run push_cmd.
    """
    name = "dockerhub"

    def publish(self, p: Product) -> PublishResult:
        img = p.artifacts.get("docker_image")
        build_cmd = self.config.get("build_cmd")
        push_cmd = self.config.get("push_cmd")

        if not img and not build_cmd:
            raise ValueError("Provide either product.artifacts['docker_image'] or config['build_cmd']")

        if build_cmd:
            subprocess.run(shlex.split(build_cmd), check=True)
        if push_cmd:
            subprocess.run(shlex.split(push_cmd), check=True)

        return PublishResult(channel=self.name, listing_url=self.config.get("image_url"), details={"image": img or build_cmd})
