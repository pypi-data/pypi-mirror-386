import importlib.util
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Optional, Union, Callable
from collections.abc import Iterator
from zoneinfo import ZoneInfo

from soar_sdk.asset import BaseAsset
from soar_sdk.input_spec import InputSpecification
from soar_sdk.compat import (
    MIN_PHANTOM_VERSION,
    PythonVersion,
)
from soar_sdk.shims.phantom_common.app_interface.app_interface import SoarRestClient
from soar_sdk.shims.phantom_common.encryption.encryption_manager_factory import (
    platform_encryption_backend,
)
from soar_sdk.abstract import SOARClient, SOARClientAuth
from soar_sdk.action_results import ActionResult
from soar_sdk.actions_manager import ActionsManager
from soar_sdk.app_cli_runner import AppCliRunner
from soar_sdk.meta.webhooks import WebhookMeta
from soar_sdk.params import Params
from soar_sdk.app_client import AppClient
from soar_sdk.action_results import ActionOutput
from soar_sdk.logging import getLogger
from soar_sdk.types import Action
from soar_sdk.webhooks.routing import Router
from soar_sdk.webhooks.models import WebhookRequest, WebhookResponse
from soar_sdk.exceptions import ActionRegistrationError

import uuid
from soar_sdk.decorators import (
    ConnectivityTestDecorator,
    ActionDecorator,
    ViewHandlerDecorator,
    OnPollDecorator,
    WebhookDecorator,
    MakeRequestDecorator,
)


def is_valid_uuid(value: str) -> bool:
    """Validates if a string is a valid UUID."""
    try:
        return str(uuid.UUID(value)).lower() == value.lower()
    except ValueError:
        return False


class App:
    """Main application class for SOAR connectors.

    This class provides the foundation for building SOAR connectors. It handles action registration, asset
    management, test connectivity, polling, and webhook functionality.

    The App class serves as the central coordinator for all app functionality,
    providing decorators for action registration and managing the lifecycle of
    SOAR operations.

    Args:
        name: Human-readable name of the app.
        app_type: Type of the app (e.g., "investigative", "corrective").
        logo: Path to the app's logo image.
        logo_dark: Path to the app's dark theme logo image.
        product_vendor: Vendor of the product this app integrates with.
        product_name: Name of the product this app integrates with.
        publisher: Publisher of the app.
        appid: Unique UUID identifier for the app.
        python_version: List of supported Python versions. Defaults to all supported versions.
        min_phantom_version: Minimum required SOAR version. Defaults to configured minimum.
        fips_compliant: Whether the app is FIPS compliant. Defaults to False.
        asset_cls: Asset class to use for configuration. Defaults to BaseAsset.

    Raises:
        ValueError: If appid is not a valid UUID.

    Example:
        >>> app = App(
        ...     name="My SOAR App",
        ...     app_type="investigative",
        ...     logo="logo.png",
        ...     logo_dark="logo_dark.png",
        ...     product_vendor="Acme Corp",
        ...     product_name="Security Platform",
        ...     publisher="My Company",
        ...     appid="12345678-1234-5678-9012-123456789012",
        ... )
    """

    def __init__(
        self,
        *,
        name: str,
        app_type: str,
        logo: str,
        logo_dark: str,
        product_vendor: str,
        product_name: str,
        publisher: str,
        appid: str,
        python_version: Optional[Union[list[PythonVersion], str]] = None,
        min_phantom_version: str = MIN_PHANTOM_VERSION,
        fips_compliant: bool = False,
        asset_cls: type[BaseAsset] = BaseAsset,
    ) -> None:
        self.asset_cls = asset_cls
        self._raw_asset_config: dict[str, Any] = {}
        self.__logger = getLogger()
        if not is_valid_uuid(appid):
            raise ValueError(f"Appid is not a valid uuid: {appid}")

        if python_version is None:
            python_version = PythonVersion.all_csv()

        self.app_meta_info = {
            "name": name,
            "type": app_type,
            "logo": logo,
            "logo_dark": logo_dark,
            "product_vendor": product_vendor,
            "product_name": product_name,
            "publisher": publisher,
            "python_version": python_version,
            "min_phantom_version": min_phantom_version,
            "fips_compliant": fips_compliant,
            "appid": appid,
        }

        self.actions_manager: ActionsManager = ActionsManager()
        self.soar_client: SOARClient = AppClient()

    def get_actions(self) -> dict[str, Action]:
        """Returns the list of actions registered in the app."""
        return self.actions_manager.get_actions()

    def cli(self) -> None:
        """Create and execute an AppRunner to run an action via command line.

        Calling this function in your app's main module will allow you to run
        actions or webhook handlers directly from the command line for testing and debugging.

        Example::

            python app.py --help
            usage: app.py [-h] [--soar-url SOAR_URL] [--soar-user SOAR_USER] [--soar-password SOAR_PASSWORD] {action,webhook} ...

            positional arguments:
            {action,webhook}
                action              Run an action
                webhook             Invoke a webhook handler

            options:
            -h, --help            show this help message and exit
            --soar-url SOAR_URL   SOAR URL to connect to. Can be provided via PHANTOM_BASE_URL environment variable as well.
            --soar-user SOAR_USER
                                    Username to connect to SOAR instance. Can be provided via PHANTOM_USER environment variable as well
            --soar-password SOAR_PASSWORD
                                    Password to connect to SOAR instance. Can be provided via PHANTOM_PASSWORD environment variable as well

        """
        runner = AppCliRunner(self)
        runner.run()

    def handle(self, raw_input_data: str, handle: Optional[int] = None) -> str:
        """Runs handling of the input data on connector.

        NOTE: handle is actually a pointer address to spawn's internal state.
        In versions of SOAR >6.4.1, handle will not be passed to the app.
        """
        input_data = InputSpecification.parse_obj(json.loads(raw_input_data))
        self._raw_asset_config = input_data.config.get_asset_config()

        # Decrypt sensitive fields in the asset configuration
        asset_id = input_data.asset_id
        for field in self.asset_cls.fields_requiring_decryption():
            if self._raw_asset_config.get(field):
                self._raw_asset_config[field] = platform_encryption_backend.decrypt(
                    self._raw_asset_config[field], str(asset_id)
                )

        # Inflate timezone fields in the asset configuration
        for field in self.asset_cls.timezone_fields():
            if field in self._raw_asset_config:
                self._raw_asset_config[field] = ZoneInfo(self._raw_asset_config[field])

        self.__logger.handler.set_handle(handle)
        soar_auth = App.create_soar_client_auth_object(input_data)
        self.soar_client.update_client(
            soar_auth, input_data.asset_id, input_data.container_id
        )
        return self.actions_manager.handle(input_data, handle=handle)

    @staticmethod
    def create_soar_client_auth_object(
        input_data: InputSpecification,
    ) -> SOARClientAuth:
        """Creates a SOARClientAuth object based on the input data.

        This is used to authenticate the SOAR client before running actions.
        """
        if input_data.user_session_token:
            return SOARClientAuth(
                user_session_token=input_data.user_session_token,
                base_url=ActionsManager.get_soar_base_url(),
            )
        elif input_data.soar_auth:
            return SOARClientAuth(
                username=input_data.soar_auth.username,
                password=input_data.soar_auth.password,
                base_url=input_data.soar_auth.phantom_url,
            )
        else:
            return SOARClientAuth(base_url=ActionsManager.get_soar_base_url())

    __call__ = handle  # the app instance can be called for ease of use by spawn3

    @property
    def asset(self) -> BaseAsset:
        """Returns the asset instance for the app."""
        if not hasattr(self, "_asset"):
            self._asset = self.asset_cls.parse_obj(self._raw_asset_config)
        return self._asset

    def register_action(
        self,
        /,
        action: Union[str, Callable],
        *,
        name: Optional[str] = None,
        identifier: Optional[str] = None,
        description: Optional[str] = None,
        verbose: str = "",
        action_type: str = "generic",  # TODO: consider introducing enum type for that
        read_only: bool = True,
        params_class: Optional[type[Params]] = None,
        output_class: Optional[type[ActionOutput]] = None,
        render_as: Optional[str] = None,
        view_handler: Union[str, Callable, None] = None,
        view_template: Optional[str] = None,
        versions: str = "EQ(*)",
        summary_type: Optional[type[ActionOutput]] = None,
        enable_concurrency_lock: bool = False,
    ) -> Action:
        """Dynamically register an action function defined in another module.

        This method allows an app to dynamically import and register an action function
        that is defined in a separate module. It provides a programmatic way to register
        actions without using decorators directly on the action function.

        Args:
            action: Either an import string to find the function that implements an action, or the imported function itself.

                .. warning::
                    If you import the function directly, and provide the callable to this function, this sometimes messes with the app's CLI invocation. For example, if you import your function with a relative import, like::

                        from .actions.my_action import my_action_function

                    then executing your app directly, like::

                        python src/app.py action my_action_function

                    will fail, but running as a module, like::

                        python -m src.app action my_action_function

                    will work. By contrast, if you use an absolute import, like::

                        from actions.my_action import my_action_function

                    then the `direct CLI invocation` will work, while the `module invocation` will fail. This is a limitation with Python itself.

                    To avoid this confusion, it is recommended to provide the action as an import string, like ``"actions.my_action:my_action_function"``. This way, both invocation methods will work consistently.


            name: Human-readable name for the action. If not provided, defaults
                to the function name with underscores replaced by spaces.
            identifier: Unique identifier for the action. If not provided, defaults
                to the function name.
            description: Brief description of what the action does. Used in the
                app manifest and UI.
            verbose: Detailed description or usage information for the action.
            action_type: Type of action (e.g., "generic", "investigate", "correct").
                Defaults to "generic".
            read_only: Whether the action only reads data without making changes.
                Defaults to True for safety.
            params_class: Pydantic model class for validating action parameters.
                If not provided, uses generic parameter validation.
            output_class: Pydantic model class for structuring action output.
                If not provided, uses generic output format.
            view_handler: Optional import string to a view handler function,
                or the imported function itself, to associate with this action.
                Will be automatically decorated with the view_handler decorator.

                .. warning::

                    See the warning above about importing action functions as opposed to using import strings. The same issues apply to view handler functions as well.

            view_template: Template name to use with the view handler. Only
                relevant if view_handler is provided.
            versions: Version constraint string for when this action is available.
                Defaults to "EQ(*)" (all versions).
            summary_type: Pydantic model class for structuring action summary output.
            enable_concurrency_lock: Whether to enable a concurrency lock for this action. Defaults to False.

        Returns:
            The registered Action instance with all metadata and handlers configured.

        Raises:
            ActionRegistrationError: If view_handler is provided but cannot be
                found in its original module for replacement.

        Example:
            >>> action = app.register_action(
            ...     "action.my_action:my_action_function",
            ...     name="Dynamic Action",
            ...     description="Action imported from another module",
            ...     view_handler="my_views_module:my_view_handler",
            ...     view_template="custom_template.html",
            ... )
        """
        if isinstance(action, str):
            action = self._resolve_function_import(action)

        if isinstance(view_handler, str):
            view_handler = self._resolve_function_import(view_handler)

        if view_handler:
            decorated_view_handler = self.view_handler(template=view_template)(
                view_handler
            )

            # Replace the function in its original module with the decorated version
            if hasattr(view_handler, "__module__") and view_handler.__module__:
                if (
                    original_module := sys.modules.get(view_handler.__module__)
                ) and hasattr(original_module, view_handler.__name__):
                    setattr(
                        original_module, view_handler.__name__, decorated_view_handler
                    )
                else:
                    raise ActionRegistrationError(
                        f"View handler {view_handler.__name__} not found in its module {view_handler.__module__}"
                    )

            view_handler = decorated_view_handler

        return self.action(
            name=name,
            identifier=identifier,
            description=description,
            verbose=verbose,
            action_type=action_type,
            read_only=read_only,
            params_class=params_class,
            output_class=output_class,
            render_as=render_as,
            view_handler=view_handler,
            versions=versions,
            summary_type=summary_type,
            enable_concurrency_lock=enable_concurrency_lock,
        )(action)

    def _resolve_function_import(self, action_path: str) -> Callable:
        """Resolves a callable action function from a dot-separated import string.

        This method takes a string representing the full import path of a function,
        imports the necessary module, and retrieves the function object.

        Args:
            action_path: Dot-separated string representing the import path of the function.
                Example: "my_module.my_submodule:my_function"

        Returns:
            The callable function object.

        Raises:
            ValueError: If the action_path is not properly formatted or if the
                module/function cannot be imported.
        """
        # Split the action_path into module and function parts,
        # handling both dot notation and file paths
        module_root = Path(inspect.stack()[2].filename).parent
        func_delim = ":" if ":" in action_path else "."
        module_name, action_func_name = action_path.rsplit(func_delim, 1)
        module_name = module_name.removesuffix(".py").replace(".", "/") + ".py"
        module_path = module_root / module_name

        module_name = (
            # Jump up from module -> src -> package root
            module_path.relative_to(module_root.parent.parent)
            # Remove .py suffix, convert to dot notation
            .with_suffix("")
            .as_posix()
            .replace("/", ".")
        )
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        # Not sure how to actually make spec None,
        # but the type hint says it's technically possible
        if spec is None or spec.loader is None:  # pragma: no cover
            raise ActionRegistrationError(action_func_name)

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            action_func = getattr(module, action_func_name)
        except Exception as e:
            raise ActionRegistrationError(action_func_name) from e

        return action_func

    def action(
        self,
        *,
        name: Optional[str] = None,
        identifier: Optional[str] = None,
        description: Optional[str] = None,
        verbose: str = "",
        action_type: str = "generic",  # TODO: consider introducing enum type for that
        read_only: bool = True,
        params_class: Optional[type[Params]] = None,
        output_class: Optional[type[ActionOutput]] = None,
        render_as: Optional[str] = None,
        view_handler: Optional[Callable] = None,
        versions: str = "EQ(*)",
        summary_type: Optional[type[ActionOutput]] = None,
        enable_concurrency_lock: bool = False,
    ) -> ActionDecorator:
        """Decorator for registering an action function.

        This decorator marks a function as an action handler for the app.
        """
        return ActionDecorator(
            app=self,
            name=name,
            identifier=identifier,
            description=description,
            verbose=verbose,
            action_type=action_type,
            read_only=read_only,
            params_class=params_class,
            output_class=output_class,
            render_as=render_as,
            view_handler=view_handler,
            versions=versions,
            summary_type=summary_type,
            enable_concurrency_lock=enable_concurrency_lock,
        )

    def test_connectivity(self) -> ConnectivityTestDecorator:
        """Decorator for registering a test connectivity function.

        This decorator marks a function as the test connectivity action for the app.
        Test connectivity is used to verify that the app can successfully connect to
        its configured external service or API. Only one test connectivity function
        is allowed per app.

        Returns:
            ConnectivityTestDecorator: A decorator instance that handles test
                connectivity registration.

        Example:
            >>> @app.test_connectivity()
            ... def test_connectivity_handler(self, asset: Asset):
            ...     logger.info(f"testing connectivity against {asset.base_url}")

        Note:
            The test connectivity function should not return anything or raise an exception if it fails.
        """
        return ConnectivityTestDecorator(self)

    def on_poll(self) -> OnPollDecorator:
        """Decorator for the on_poll action.

        The decorated function must be a generator (using yield) or return an Iterator that yields Container and/or Artifact objects. Only one on_poll action is allowed per app.

        Usage:
        If a Container is yielded first, all subsequent Artifacts will be added to that container unless they already have a `container_id`.
        If an `Artifact` is yielded without a container and no `container_id` is set, it will be skipped.

        Example:
            >>> @app.on_poll()
            ... def on_poll(
            ...     params: OnPollParams, soar: SOARClient, asset: Asset
            ... ) -> Iterator[Union[Container, Artifact]]:
            ...     yield Container(
            ...         name="Network Alerts",
            ...         description="Some network-related alerts",
            ...         severity="medium",
            ...     )
        """
        return OnPollDecorator(self)

    def view_handler(
        self,
        *,
        template: Optional[str] = None,
    ) -> ViewHandlerDecorator:
        """Decorator for custom view functions with output parsing and template rendering.

        The decorated function receives parsed ActionOutput objects and can return either a dict for template rendering, HTML string, or component data model.
        If a template is provided, dict results will be rendered using the template. Component type is automatically inferred from the return type annotation.

        .. seealso::

            For more information on custom views, see the following :doc:`custom views documentation </custom_views/index>`:

        Example:
            >>> @app.view_handler(template="my_template.html")
            ... def my_view(outputs: List[MyActionOutput]) -> dict:
            ...     return {"data": outputs[0].some_field}

            >>> @app.view_handler()
            ... def my_chart_view(outputs: List[MyActionOutput]) -> PieChartData:
            ...     return PieChartData(
            ...         title="Chart",
            ...         labels=["A", "B"],
            ...         values=[1, 2],
            ...         colors=["red", "blue"],
            ...     )
        """
        return ViewHandlerDecorator(self, template=template)

    def make_request(
        self, output_class: Optional[type[ActionOutput]] = None
    ) -> MakeRequestDecorator:
        """Decorator for registering a ``make request`` action function.

        This decorator marks a function as the ``make request`` action for the app. ``make request`` is used to call any endpoint of the underlying API service this app implements.
        Only one ``make request`` action is allowed per app. The function you define needs to accept at least one parameter of type :class:`~soar_sdk.params.MakeRequestParams` and can accept any other parameters you need.
        Other useful parameters to accept are the SOARClient and the asset.

        Returns:
            MakeRequestActionDecorator: A decorator instance that handles ``make request`` action registration.

        Example:
            >>> @app.make_request()
            ... def http_action(
            ...     self, params: MakeRequestParams, asset: Asset
            ... ) -> MakeRequestOutput:
            ...     logger.info(f"testing connectivity against {asset.base_url}")
            ...     return MakeRequestOutput(
            ...         status_code=200,
            ...         response_body=f"Base url is {asset.base_url}",
            ...     )

        Note:
            The ``make request`` action function should return either a :class:`~soar_sdk.action_results.MakeRequestOutput` object or of an output class derived from it.
        """
        return MakeRequestDecorator(self, output_class=output_class)

    @staticmethod
    def _validate_params_class(
        action_name: str,
        spec: inspect.FullArgSpec,
        params_class: Optional[type[Params]] = None,
    ) -> type[Params]:
        """Validates the class used for params argument of the action.

        Ensures the class is defined and provided as it is also used for building
        the manifest JSON file.
        """
        # validating params argument
        validated_params_class = params_class or Params
        if params_class is None:
            # try to fetch from the function args typehints
            if not len(spec.args):
                raise TypeError(
                    "Action function must accept at least the params positional argument"
                )
            params_arg = spec.args[0]
            annotated_params_type: Optional[type] = spec.annotations.get(params_arg)
            if annotated_params_type is None:
                raise TypeError(
                    f"Action {action_name} has no params type set. "
                    "The params argument must provide type which is derived "
                    "from Params class"
                )
            if issubclass(annotated_params_type, Params):
                validated_params_class = annotated_params_type
            else:
                raise TypeError(
                    f"Proper params type for action {action_name} is not derived from Params class."
                )
        return validated_params_class

    def _build_magic_args(self, function: Callable, **kwargs: object) -> dict[str, Any]:
        """Builds the auto-magic optional arguments for an action function.

        This is used to pass the soar client and asset to the action function, when requested.
        """
        # The reason we wrap values in callables is to avoid evaluating any lazy attributes
        # (like asset) unless they're actually going to be used in the action function.
        magic_args: dict[str, Union[object, Callable[[], object]]] = {
            "soar": self.soar_client,
            "asset": lambda: self.asset,
        }

        sig = inspect.signature(function)
        for name, value_or_getter in magic_args.items():
            given_value = kwargs.pop(name, None)
            if name in sig.parameters:
                # Give the original kwargs precedence over the magic args
                value = (
                    value_or_getter() if callable(value_or_getter) else value_or_getter
                )
                kwargs[name] = given_value or value

        return kwargs

    @staticmethod
    def _validate_params(params: Params, action_name: str) -> Params:
        """Validates input params, checking them against the use of proper Params class inheritance.

        This is automatically covered by AppClient, but can be also useful for when
        using in testing with mocked SOARClient implementation.
        """
        if not isinstance(params, Params):
            raise TypeError(
                f"Provided params are not inheriting from Params class for action {action_name}"
            )
        return params

    @staticmethod
    def _adapt_action_result(
        result: Union[
            ActionOutput,
            ActionResult,
            list[ActionOutput],
            Iterator[ActionOutput],
            tuple[bool, str],
            bool,
        ],
        actions_manager: ActionsManager,
        action_params: Optional[Params] = None,
        message: str = "",
        summary: Optional[ActionOutput] = None,
    ) -> bool:
        """Handles multiple ways of returning response from action.

        The simplest result can be returned from the action as a tuple of success
        boolean value and an extra message to add.

        For backward compatibility, it also supports returning ActionResult object as
        in the legacy Connectors.
        """
        if type(result) is list or isinstance(result, Iterator):
            statuses = []
            for item in result:
                statuses.append(
                    App._adapt_action_result(
                        item, actions_manager, action_params, message, summary
                    )
                )
            # Handle empty list/iterator case
            if not statuses:
                result = ActionOutput(status=True, message=message)
            else:
                return all(statuses)

        if isinstance(result, ActionOutput):
            output_dict = result.dict(by_alias=True)
            param_dict = action_params.dict() if action_params else None

            result = ActionResult(
                status=True,
                message=message,
                param=param_dict,
            )
            result.add_data(output_dict)
            if summary:
                result.set_summary(summary.dict(by_alias=True))

        if isinstance(result, ActionResult):
            actions_manager.add_result(result)
            return result.get_status()
        if isinstance(result, tuple) and 2 <= len(result) <= 3:
            action_result = ActionResult(*result)
            actions_manager.add_result(action_result)
            return result[0]
        return False

    @staticmethod
    def _dev_skip_in_pytest(function: Callable, inner: Action) -> None:
        """When running pytest, all actions with a name starting with test_ will be treated as test.

        This method will mark them as to be skipped.
        """
        if "pytest" in sys.modules and function.__name__.startswith("test_"):
            # importing locally to not require this package in the runtime requirements
            import pytest

            pytest.mark.skip(inner)

    webhook_meta: Optional[WebhookMeta] = None
    webhook_router: Optional[Router] = None

    def enable_webhooks(
        self,
        default_requires_auth: bool = True,
        default_allowed_headers: Optional[list[str]] = None,
        default_ip_allowlist: Optional[list[str]] = None,
    ) -> "App":
        """Enable webhook functionality for the app.

        This method configures the app to handle incoming webhook requests by setting
        up the security and routing configurations.

        Args:
            default_requires_auth: Whether webhooks require authentication by default.
            default_allowed_headers: List of HTTP headers allowed in webhook requests.
            default_ip_allowlist: List of IP addresses/CIDR blocks allowed to send webhooks.
                Defaults to ["0.0.0.0/0", "::/0"] (allow all).

        Returns:
            The App instance for method chaining.

        Example:
            >>> app.enable_webhooks(
            ...     default_requires_auth=True,
            ...     default_allowed_headers=["X-Custom-Header"],
            ...     default_ip_allowlist=["192.168.1.0/24"],
            ... )
        """
        if default_allowed_headers is None:
            default_allowed_headers = []
        if default_ip_allowlist is None:
            default_ip_allowlist = ["0.0.0.0/0", "::/0"]

        self.webhook_meta = WebhookMeta(
            handler=None,  # The handler is set by the ManifestProcessor when generating the final manifest
            requires_auth=default_requires_auth,
            allowed_headers=default_allowed_headers,
            ip_allowlist=default_ip_allowlist,
        )

        self.webhook_router = Router()

        return self

    def webhook(
        self, url_pattern: str, allowed_methods: Optional[list[str]] = None
    ) -> WebhookDecorator:
        """Decorator for registering a webhook handler."""
        return WebhookDecorator(self, url_pattern, allowed_methods)

    def handle_webhook(
        self,
        method: str,
        headers: dict[str, str],
        path_parts: list[str],
        query: dict[str, Union[str, list[str], None]],
        body: Optional[str],
        asset: dict,
        soar_rest_client: SoarRestClient,
    ) -> dict:
        """Handles the incoming webhook request."""
        if self.webhook_router is None:
            raise RuntimeError("Webhooks are not enabled for this app.")

        self._raw_asset_config = asset

        _, soar_auth_token = soar_rest_client.session.headers["Cookie"].split("=")
        asset_id = soar_rest_client.asset_id
        soar_base_url = soar_rest_client.base_url
        soar_auth = SOARClientAuth(
            user_session_token=soar_auth_token,
            base_url=soar_base_url,
        )
        self.soar_client.update_client(soar_auth, asset_id)

        normalized_query = {}
        for key, value in query.items():
            # Normalize query parameters to always be a list
            # This is needed because SOAR prior to 7.0.0 used to flatten query parameters to the last item per key
            # SOAR 7.0.0+ will normalize all query parameters to lists, with an "empty" parameter expressed as a list containing an empty string
            if value is None:
                normalized_query[key] = [""]
            elif isinstance(value, list):
                normalized_query[key] = value
            else:
                normalized_query[key] = [value]

        request = WebhookRequest(
            method=method,
            headers=headers,
            path_parts=path_parts,
            query=normalized_query,
            body=body,
            asset=self.asset,
            soar_auth_token=soar_auth_token,
            soar_base_url=soar_base_url,
            asset_id=asset_id,
        )

        response = self.webhook_router.handle_request(request)
        if not isinstance(response, WebhookResponse):
            raise TypeError(
                f"Webhook handler must return a WebhookResponse, got {type(response)}"
            )
        return response.dict()
