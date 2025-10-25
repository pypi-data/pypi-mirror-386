from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from .base import (
    DetectResult,
    DependencySpec,
    Provider,
    _exists,
    MountSpec,
    ServiceSpec,
    VolumeSpec,
    CustomCommands,
)


class PhpProvider:
    def __init__(self, path: Path, custom_commands: CustomCommands):
        self.path = path
        self.custom_commands = custom_commands
        self.has_composer = _exists(self.path, "composer.json", "composer.lock") or (
            custom_commands.install and custom_commands.install.startswith("composer ")
        )

    @classmethod
    def name(cls) -> str:
        return "php"

    @classmethod
    def detect(
        cls, path: Path, custom_commands: CustomCommands
    ) -> Optional[DetectResult]:
        if _exists(path, "composer.json") and _exists(path, "public/index.php"):
            return DetectResult(cls.name(), 60)
        if (
            _exists(path, "index.php")
            or _exists(path, "public/index.php")
            or _exists(path, "app/index.php")
        ):
            return DetectResult(cls.name(), 10)
        if custom_commands.start and custom_commands.start.startswith("php "):
            return DetectResult(cls.name(), 70)
        if custom_commands.install and custom_commands.install.startswith("composer "):
            return DetectResult(cls.name(), 30)
        return None

    def initialize(self) -> None:
        pass

    def serve_name(self) -> str:
        return self.path.name

    def platform(self) -> Optional[str]:
        return None

    def dependencies(self) -> list[DependencySpec]:
        deps = [
            DependencySpec(
                "php",
                env_var="SHIPIT_PHP_VERSION",
                default_version="8.3",
                architecture_var="SHIPIT_PHP_ARCHITECTURE",
                use_in_build=True,
                use_in_serve=True,
            ),
        ]
        if self.has_composer:
            deps.append(DependencySpec("composer", use_in_build=True))
            deps.append(DependencySpec("bash", use_in_serve=True))
        return deps

    def declarations(self) -> Optional[str]:
        if self.has_composer:
            return 'HOME = getenv("HOME")\n'
        return None

    def build_steps(self) -> list[str]:
        steps = [
            'workdir(app["build"])',
        ]
        if _exists(self.path, "php.ini"):
            steps.append('copy("php.ini", "{}/php.ini".format(assets["build"]))')
        else:
            steps.append(
                'copy("php/php.ini", "{}/php.ini".format(assets["build"]), base="assets")'
            )

        if self.has_composer:
            steps.append('env(HOME=HOME, COMPOSER_FUND="0")')
            steps.append(
                'run("composer install --optimize-autoloader --no-scripts --no-interaction", inputs=["composer.json", "composer.lock"], outputs=["."], group="install")'
            )

        steps.append('copy(".", ".", ignore=[".git"])')
        return steps

    def prepare_steps(self) -> Optional[list[str]]:
        return None

    def commands(self) -> Dict[str, str]:
        commands = self.base_commands()
        if self.custom_commands.start:
            commands["start"] = json.dumps(self.custom_commands.start)
        return commands

    def base_commands(self) -> Dict[str, str]:
        if _exists(self.path, "public/index.php"):
            return {
                "start": '"php -S localhost:{} -t {}/public".format(PORT, app["serve"])'
            }
        elif _exists(self.path, "app/index.php"):
            return {
                "start": '"php -S localhost:{} -t {}/app".format(PORT, app["serve"])'
            }
        elif _exists(self.path, "index.php"):
            return {"start": '"php -S localhost:{} -t {}".format(PORT, app["serve"])'}
        return {
            "start": '"php -S localhost:{} -t {}".format(PORT, app["serve"])',
        }

    def mounts(self) -> list[MountSpec]:
        return [
            MountSpec("app"),
            MountSpec("assets"),
        ]

    def volumes(self) -> list[VolumeSpec]:
        return []

    def env(self) -> Optional[Dict[str, str]]:
        return {
            "PHP_INI_SCAN_DIR": '"{}".format(assets["serve"])',
        }

    def services(self) -> list[ServiceSpec]:
        return []
