import argparse
import inspect
import json
from pathlib import Path
import typing
from typing import Optional, Any
import os
from pydantic import ValidationError
from urllib.parse import urlparse, parse_qs

from soar_sdk.input_spec import ActionParameter, AppConfig, InputSpecification, SoarAuth
from soar_sdk.shims.phantom_common.encryption.encryption_manager_factory import (
    platform_encryption_backend,
)
from soar_sdk.types import Action
from soar_sdk.webhooks.models import WebhookRequest
from soar_sdk.logging import PhantomLogger
from soar_sdk.shims.phantom_common.app_interface.app_interface import SoarRestClient
from soar_sdk.abstract import SOARClientAuth

if typing.TYPE_CHECKING:
    from .app import App


class AppCliRunner:
    """Runner for local run of the actions handling with the app.

    Generates subparsers for each action, which take in JSON files for parameters and assets.
    """

    def __init__(self, app: "App") -> None:
        self.app = app

    def parse_args(self, argv: Optional[list[str]] = None) -> argparse.Namespace:
        """Parse command line arguments for the app CLI runner."""
        root_parser = argparse.ArgumentParser()
        root_parser.add_argument(
            "--soar-url",
            default=os.getenv("PHANTOM_BASE_URL"),
            help="SOAR URL to connect to. Can be provided via PHANTOM_BASE_URL environment variable as well.",
        )
        root_parser.add_argument(
            "--soar-user",
            default=os.getenv("PHANTOM_USER"),
            help="Username to connect to SOAR instance. Can be provided via PHANTOM_USER environment variable as well",
        )
        root_parser.add_argument(
            "--soar-password",
            default=os.getenv("PHANTOM_PASSWORD"),
            help="Password to connect to SOAR instance. Can be provided via PHANTOM_PASSWORD environment variable as well",
        )

        subparsers = root_parser.add_subparsers()
        subparsers.required = True

        actions_parser = subparsers.add_parser("action", help="Run an action")
        action_subparsers = actions_parser.add_subparsers(
            dest="action", title="Actions"
        )
        action_subparsers.required = True
        for name, action in self.app.actions_manager.get_actions().items():
            parser = action_subparsers.add_parser(
                name,
                aliases=(action.meta.action.replace(" ", "-"),),
                help=action.meta.verbose,
            )
            parser.set_defaults(identifier=name)
            parser.set_defaults(action=action)

            needs_asset = "asset" in inspect.signature(action).parameters
            parser.set_defaults(needs_asset=needs_asset)
            if needs_asset:
                parser.add_argument(
                    "-a",
                    "--asset-file",
                    help="Path to the asset file",
                    type=Path,
                    required=True,
                )

            if action.params_class is not None:
                parser.add_argument(
                    "-p", "--param-file", help="Input parameter JSON file", type=Path
                )

        webhooks_parser = subparsers.add_parser(
            "webhook", help="Invoke a webhook handler"
        )
        webhooks_parser.add_argument("url", help="Webhook URL to invoke")
        webhooks_parser.set_defaults(needs_asset=True)
        webhooks_parser.add_argument(
            "-a",
            "--asset-file",
            help="Path to the asset file",
            type=Path,
            required=True,
        )
        webhooks_parser.add_argument(
            "--asset-id",
            help="ID of the asset the webhook is tied to",
            type=int,
            default=1,
        )
        webhooks_parser.add_argument(
            "-X",
            "--method",
            "--request",
            choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
            default="GET",
            help="HTTP method to use for the webhook request",
        )
        webhooks_parser.add_argument(
            "-H",
            "--header",
            action="append",
            help="HTTP header to include in the request. Can be specified multiple times.",
            metavar="HEADER=VALUE",
        )
        webhooks_parser.add_argument(
            "-d",
            "--data",
            help="Data to include in the request body. If not provided, the request will be empty.",
        )

        # By default, argv will be None and we'll fall back to sys.argv,
        # but making it possible to provide args makes this method unit testable.
        args = root_parser.parse_args(argv)

        asset_json: dict[str, Any] = {}
        if args.needs_asset:
            try:
                asset_json = json.loads(args.asset_file.read_text())
            except Exception as e:
                root_parser.error(
                    f"Unable to read asset JSON file {args.asset_file}: {e}"
                )

        if chosen_action := getattr(args, "action", None):
            self._parse_action_args(chosen_action, args, root_parser, asset_json)

        if webhook_url := getattr(args, "url", None):
            self._parse_webhook_args(webhook_url, args, root_parser, asset_json)

        return args

    def _parse_action_args(
        self,
        chosen_action: Action,
        args: argparse.Namespace,
        root_parser: argparse.ArgumentParser,
        asset_json: dict[str, Any],
    ) -> None:
        parameter_list: list[ActionParameter] = []

        if chosen_action.params_class is not None:
            params_file: Path = args.param_file
            try:
                params_json = json.loads(params_file.read_text())
            except Exception as e:
                root_parser.error(
                    f"Unable to read parameter JSON file {params_file}: {e}"
                )

            try:
                param = chosen_action.params_class.parse_obj(params_json)
            except Exception as e:
                root_parser.error(
                    f"Unable to parse parameter JSON file {params_file}:\n{e}"
                )

            parameter_list.append(ActionParameter(**param.dict()))

        input_data = InputSpecification(
            action=args.identifier,
            identifier=args.identifier,
            # FIXME: Make these values real
            config=AppConfig(
                app_version="1.0.0",
                directory=".",
                main_module="example_connector.py",
            ),
            parameters=parameter_list,
        )

        # If any the asset fields are sensitive, encrypt them with the fake encyption_helper, since that's what the handler is expecting.
        fields_to_encrypt = self.app.asset_cls.fields_requiring_decryption()
        for field, value in asset_json.items():
            if field in fields_to_encrypt:
                asset_json[field] = platform_encryption_backend.encrypt(
                    value, str(input_data.asset_id)
                )

        input_data.config = AppConfig(
            **input_data.config.dict(),
            **asset_json,  # Merge asset JSON into config
        )

        soar_args = (args.soar_url, args.soar_user, args.soar_password)
        if any(soar_args):
            try:
                auth = SoarAuth(
                    phantom_url=args.soar_url,
                    username=args.soar_user,
                    password=args.soar_password,
                )
                input_data.soar_auth = auth
            except ValidationError as e:
                root_parser.error(f"Provided soar auth arguments are invalid: {e}.")

        args.raw_input_data = input_data.json()

    def _parse_webhook_args(
        self,
        webhook_url: str,
        args: argparse.Namespace,
        root_parser: argparse.ArgumentParser,
        asset_json: dict[str, Any],
    ) -> None:
        parsed = urlparse(webhook_url)

        path = parsed.path
        query = parse_qs(parsed.query)

        path_parts = path.strip("/").split("/")

        headers: dict[str, str] = {}
        for header in args.header or []:
            if "=" not in header:
                root_parser.error(
                    f"Invalid header format: {header}. Expected format is HEADER=VALUE."
                )
            h_key, h_value = header.split("=", 1)
            headers[h_key] = h_value

        soar_base_url = args.soar_url or "https://example.com"
        soar_auth_token = ""
        soar_args = (soar_base_url, args.soar_user, args.soar_password)
        if all(soar_args):
            auth = SOARClientAuth(
                base_url=soar_base_url,
                username=args.soar_user,
                password=args.soar_password,
            )
            self.app.soar_client.update_client(auth, args.asset_id)
            soar_auth_token = self.app.soar_client.client.cookies.get("sessionid") or ""

        args.webhook_request = WebhookRequest(
            method=args.method,
            headers=headers,
            path_parts=path_parts,
            query=query,
            body=args.data,
            asset=self.app.asset_cls.parse_obj(asset_json),
            soar_base_url=soar_base_url,
            soar_auth_token=soar_auth_token,
            asset_id=args.asset_id,
        )
        print(f"Parsed webhook request: {args.webhook_request}")

    def run(self, argv: Optional[list[str]] = None) -> None:
        """Run the app CLI."""
        args = self.parse_args(argv=argv)

        logger = PhantomLogger()

        if input_data := getattr(args, "raw_input_data", None):
            self.app.handle(input_data)
            for result in self.app.actions_manager.get_action_results():
                params_pretty = json.dumps(result.param, indent=2, ensure_ascii=False)
                data_pretty = json.dumps(
                    result.get_data(), indent=2, ensure_ascii=False
                )

                logger.info(f"Action params: {params_pretty}")
                logger.info(f"Action success: {result.get_status()}")
                logger.info(f"Result data: {data_pretty}")
                logger.info(f"Result summary: {result.get_summary()}")
                logger.info(f"Result message: {result.get_message()}")
                logger.info(f"Objects successful/total: {int(result.get_status())}/1")

        if webhook_request := getattr(args, "webhook_request", None):
            soar_rest_client = SoarRestClient(
                token=webhook_request.soar_auth_token, asset_id=webhook_request.asset_id
            )
            soar_rest_client.base_url = webhook_request.soar_base_url
            response = self.app.handle_webhook(
                method=webhook_request.method,
                headers=webhook_request.headers,
                path_parts=webhook_request.path_parts,
                query=webhook_request.query,
                body=webhook_request.body,
                asset=webhook_request.asset,
                soar_rest_client=soar_rest_client,
            )

            status_code = response["status_code"]
            logger.info(f"Response status code: {status_code}\n")

            logger.info("Response headers:")
            for name, value in response.get("headers", []):
                logger.info(f"{name}: {value}")
            logger.info("")

            if response.get("is_base64_encoded", False):
                logger.info("Response content (base64-encoded):")
            else:
                logger.info("Response content:")
            logger.info(response.get("content", ""))
