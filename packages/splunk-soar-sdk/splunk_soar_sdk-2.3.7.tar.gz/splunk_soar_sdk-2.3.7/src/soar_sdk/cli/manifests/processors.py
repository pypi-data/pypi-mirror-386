import importlib
import json
import toml
from datetime import datetime, timezone
from pathlib import Path
from pprint import pprint

from soar_sdk.app import App
from soar_sdk.cli.path_utils import context_directory
from soar_sdk.compat import remove_when_soar_newer_than, UPDATE_TIME_FORMAT
from soar_sdk.meta.adapters import TOMLDataAdapter
from soar_sdk.meta.app import AppMeta
from soar_sdk.meta.dependencies import UvLock


class ManifestProcessor:
    """Class responsible for generating app manifest JSON files.

    Loads app metadata into AppMeta object, and further converts that into the JSON format
    Splunk SOAR expects.
    """

    def __init__(self, manifest_path: str, project_context: str = ".") -> None:
        self.manifest_path = manifest_path
        self.project_context = Path(project_context)

    def build(self, is_sdk_locally_built: bool = False) -> AppMeta:
        """Builds full AppMeta information including actions and other extra fields."""
        app_meta: AppMeta = self.load_toml_app_meta()
        app = self.import_app_instance(app_meta)
        app_meta.configuration = app.asset_cls.to_json_schema()
        app_meta.actions = app.actions_manager.get_actions_meta_list()
        app_meta.utctime_updated = datetime.now(timezone.utc).strftime(
            UPDATE_TIME_FORMAT
        )
        for field, value in app.app_meta_info.items():
            setattr(app_meta, field, value)

        uv_lock = self.load_app_uv_lock()
        dependencies = uv_lock.build_package_list(app_meta.project_name)
        if is_sdk_locally_built:
            dependencies[:] = [
                dep for dep in dependencies if dep.name != "splunk-soar-sdk"
            ]

        app_meta.pip39_dependencies, app_meta.pip313_dependencies = (
            uv_lock.resolve_dependencies(dependencies)
        )

        if app.webhook_meta is not None:
            remove_when_soar_newer_than("6.4.0")
            app_meta.webhook = app.webhook_meta
            app_meta.webhook.handler = (
                f"{app_meta.main_module.replace(':', '.')}.handle_webhook"
            )

        return app_meta

    def create(self) -> None:
        """Creates the App Manifest JSON and saves it back to the manifest file."""
        app_meta = self.build()
        pprint(app_meta.to_json_manifest())

        self.save_json_manifest(app_meta)

    def load_toml_app_meta(self) -> AppMeta:
        """Parses app metadata from a pyproject.toml file into an AppMeta object."""
        return TOMLDataAdapter.load_data(
            f"{self.project_context.as_posix()}/pyproject.toml"
        )

    def load_app_uv_lock(self) -> UvLock:
        """Parses an app's uv.lock file into a UvLock model object."""
        with (self.project_context / "uv.lock").open() as f:
            lockfile = toml.load(f)
        return UvLock(**lockfile)

    def save_json_manifest(self, app_meta: AppMeta) -> None:
        """Writes an AppMeta object into an app manifest JSON file on disk."""
        with open(self.manifest_path, "w") as f:
            json.dump(app_meta.to_json_manifest(), f, indent=4)

    @staticmethod
    def get_module_dot_path(main_module: str) -> str:
        """Converts main_module setting from pyproject.toml into importable module dot-path.

        Example:
            src/app.py:app -> src.app
        """
        module_path = main_module.split(":")[0]
        module_path = module_path.removesuffix(".py")
        module_path = module_path.removesuffix(".pyc")
        return module_path.replace("/", ".")

    def import_app_instance(self, app_meta: AppMeta) -> App:
        """Given an AppMeta; finds, imports, and returns an app's central App object."""
        module_name = self.get_module_dot_path(app_meta.main_module)
        app_instance_name = app_meta.main_module.split(":")[-1]

        with context_directory(self.project_context):
            # operate as if running in the project context directory
            package_name = Path.cwd().name
            app_module = importlib.import_module(f"{package_name}.{module_name}")
            app = getattr(app_module, app_instance_name)
        return app
