import toml

from .app import AppMeta


class TOMLDataAdapter:
    """Parses app metadata from a pyproject.toml file into an AppMeta object."""

    @staticmethod
    def load_data(filepath: str) -> AppMeta:
        """Load the app metadata from the given path to a pyproject.toml into an AppMeta."""
        with open(filepath) as f:
            toml_data = toml.load(f)

        uv_app_data = toml_data.get("project", {})
        sdk_tool_data = toml_data.get("tool", {}).get("soar", {}).get("app", {})
        project_name = uv_app_data.get("name")
        package_name = (
            f"phantom_{project_name}"
            if project_name and not project_name.startswith("phantom_")
            else project_name
        )

        return AppMeta(
            **dict(
                description=uv_app_data.get("description"),
                app_version=uv_app_data.get("version"),
                license=uv_app_data.get("license"),
                package_name=package_name,
                project_name=project_name,
                main_module=sdk_tool_data.get("main_module"),
            )
        )
