from io import BytesIO
from collections.abc import Iterator
from unittest import mock
import json
from pathlib import Path
import pytest
import pytest_mock

from soar_sdk.action_results import ActionOutput
from soar_sdk.app import App
from soar_sdk.app_cli_runner import AppCliRunner
import os

from soar_sdk.params import Params
from soar_sdk.webhooks.models import WebhookRequest, WebhookResponse
from soar_sdk.asset import AssetField, BaseAsset


class Asset(BaseAsset):
    base_url: str


@pytest.fixture
def tmp_asset_and_param_files(tmp_path: Path) -> Iterator[tuple[Path, Path]]:
    """Fixture to create temporary asset and parameter files, already opened for writing."""
    asset_file = tmp_path / "asset.json"
    param_file = tmp_path / "params.json"

    yield asset_file, param_file

    asset_file.unlink(missing_ok=True)
    param_file.unlink(missing_ok=True)


def test_parse_args_with_no_actions(simple_app: App, mocker: pytest_mock.MockerFixture):
    """Test parsing arguments when app has no actions."""
    runner = AppCliRunner(simple_app)

    # Mock get_actions to return an empty dict
    mocker.patch.object(runner.app.actions_manager, "get_actions", return_value={})

    # Calling parse_args with no argv should raise SystemExit because subparser is required
    with pytest.raises(SystemExit):
        runner.parse_args([])


def test_parse_args_with_action_no_params(app_with_action: App):
    """Test parsing arguments for an action that doesn't require params or asset."""
    runner = AppCliRunner(app_with_action)

    # Get the real action from our fixture
    action = runner.app.actions_manager.get_action("test_action")
    assert action is not None

    # Modify the action to not require params
    action.params_class = None

    # Parse args with our action
    args = runner.parse_args(["action", "test_action"])

    # Verify the returned args have the expected values
    assert args.identifier == "test_action"
    assert args.action == action
    assert not args.needs_asset


def test_parse_args_with_action_needs_asset(
    app_with_asset_action: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test parsing arguments for an action that requires an asset file."""
    runner = AppCliRunner(app_with_asset_action)
    # Get the real action from our fixture
    action = runner.app.actions_manager.get_action("test_action_with_asset")
    assert action is not None

    asset_file, param_file = tmp_asset_and_param_files

    asset_json = {"key": "value"}
    asset_file.write_text(json.dumps(asset_json))

    param_json = {"field1": 42}
    param_file.write_text(json.dumps(param_json))

    # Parse args with our action and asset file
    args = runner.parse_args(
        [
            "action",
            "test_action_with_asset",
            "--asset-file",
            asset_file.as_posix(),
            "--param-file",
            param_file.as_posix(),
        ]
    )

    # Verify the returned args have the expected values
    assert args.identifier == "test_action_with_asset"
    assert args.action == action
    assert args.needs_asset
    assert args.asset_file == asset_file


def test_parse_args_with_action_needs_params(
    app_with_action: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test parsing arguments for an action that requires parameters."""
    runner = AppCliRunner(app_with_action)

    # Get the real action from our fixture
    action = runner.app.actions_manager.get_action("test_action")
    assert action is not None

    _, param_file = tmp_asset_and_param_files

    param_json = {"field1": 42}
    param_file.write_text(json.dumps(param_json))

    # Parse args with our action and param file
    args = runner.parse_args(
        ["action", "test_action", "--param-file", param_file.as_posix()]
    )

    # Verify the returned args have the expected values
    assert args.identifier == "test_action"
    assert args.action == action
    assert not args.needs_asset
    assert args.param_file == param_file

    # Verify that raw_input_data is properly created
    input_data = json.loads(args.raw_input_data)
    assert input_data["action"] == "test_action"
    assert input_data["identifier"] == "test_action"
    assert input_data["config"]["app_version"] == "1.0.0"
    assert len(input_data["parameters"]) == 1
    assert input_data["parameters"][0]["field1"] == 42


def test_parse_args_with_action_needs_asset_and_params(
    app_with_asset_action: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test parsing arguments for an action that requires both asset and parameters."""
    runner = AppCliRunner(app_with_asset_action)

    # Get the real action from our fixture
    action = runner.app.actions_manager.get_action("test_action_with_asset")
    assert action is not None

    asset_file, param_file = tmp_asset_and_param_files

    asset_json = {"asset_key": "asset_value"}
    asset_file.write_text(json.dumps(asset_json))

    param_json = {"field1": 99}
    param_file.write_text(json.dumps(param_json))

    # Parse args with our action, asset file and param file
    args = runner.parse_args(
        [
            "action",
            "test_action_with_asset",
            "--asset-file",
            asset_file.as_posix(),
            "--param-file",
            param_file.as_posix(),
        ]
    )

    # Verify the returned args have the expected values
    assert args.identifier == "test_action_with_asset"
    assert args.action == action
    assert args.needs_asset
    assert args.asset_file == asset_file
    assert args.param_file == param_file

    # Verify that raw_input_data is properly created with asset data
    input_data = json.loads(args.raw_input_data)
    assert input_data["action"] == "test_action_with_asset"
    assert input_data["identifier"] == "test_action_with_asset"
    assert input_data["config"]["app_version"] == "1.0.0"
    assert input_data["config"]["asset_key"] == "asset_value"
    assert "parameters" in input_data
    if action.params_class:  # Check if the action actually has params
        assert len(input_data["parameters"]) == 1
        assert input_data["parameters"][0]["field1"] == 99


def test_parse_args_with_invalid_param_file(
    app_with_action: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test parsing arguments with an invalid parameter file."""
    runner = AppCliRunner(app_with_action)

    _, param_file = tmp_asset_and_param_files

    # Create a temporary param file with invalid JSON content
    param_file.write_text("this is not valid json")

    # Parsing args with invalid param file should raise SystemExit
    with pytest.raises(SystemExit):
        runner.parse_args(
            ["action", "test_action", "--param-file", param_file.as_posix()]
        )


def test_parse_args_with_invalid_asset_file(
    app_with_asset_action: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test parsing arguments with an invalid asset file."""
    runner = AppCliRunner(app_with_asset_action)

    asset_file, _ = tmp_asset_and_param_files

    # Create a temporary asset file with invalid JSON content
    asset_file.write_text("this is not valid json")

    # Parsing args with invalid asset file should raise SystemExit
    with pytest.raises(SystemExit):
        runner.parse_args(
            ["action", "test_action_with_asset", "--asset-file", asset_file.as_posix()]
        )


def test_parse_args_with_malformed_param_values(
    app_with_action: App,
    tmp_asset_and_param_files: tuple[Path, Path],
    mocker: pytest_mock.MockerFixture,
):
    """Test parsing arguments with valid JSON but invalid parameter values."""
    runner = AppCliRunner(app_with_action)

    # Get the real action from our fixture
    action = runner.app.actions_manager.get_action("test_action")
    assert action is not None
    assert action.params_class is not None

    param_file, _ = tmp_asset_and_param_files

    # Create a temporary param file with valid JSON but incompatible data types
    param_json = {"field1": "not_an_integer"}  # field1 expects an integer
    param_file.write_text(json.dumps(param_json))

    # Parsing args with invalid param values should raise SystemExit
    with pytest.raises(SystemExit):
        runner.parse_args(
            ["action", "test_action", "--param-file", param_file.as_posix()]
        )


def test_with_soar_authentication(
    app_with_action: App, mock_get_any_soar_call, mock_post_any_soar_call
):
    """Test parsing arguments for an action that requires both asset and parameters."""
    runner = AppCliRunner(app_with_action)

    # Get the real action from our fixture
    action = runner.app.actions_manager.get_action("test_action")
    assert action is not None
    action.params_class = None
    os.environ["PHANTOM_PASSWORD"] = "password"

    args = runner.parse_args(
        [
            "--soar-url",
            "10.34.5.6",
            "--soar-user",
            "soar_local_admin",
            "action",
            "test_action",
        ]
    )
    del os.environ["PHANTOM_PASSWORD"]

    assert args.soar_url == "10.34.5.6"
    assert args.soar_user == "soar_local_admin"
    assert args.soar_password == "password"

    input_data = json.loads(args.raw_input_data)
    assert input_data["soar_auth"]["phantom_url"] == "https://10.34.5.6"
    assert input_data["soar_auth"]["username"] == "soar_local_admin"
    assert input_data["soar_auth"]["password"] == "password"


def test_bas_soar_auth_params(app_with_action: App):
    """Test parsing arguments for an action that requires both asset and parameters."""
    runner = AppCliRunner(app_with_action)

    # Get the real action from our fixture
    action = runner.app.actions_manager.get_action("test_action")
    assert action is not None
    action.params_class = None

    with pytest.raises(SystemExit):
        runner.parse_args(
            [
                "--soar-url",
                "10.34.5.6",
                "--soar-user",
                "soar_local_admin",
                "action",
                "test_action",
            ]
        )


def test_parse_args_webhook(
    app_with_asset_webhook: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test parsing arguments for a webhook."""
    runner = AppCliRunner(app_with_asset_webhook)

    asset_file, _ = tmp_asset_and_param_files
    asset_json = {"base_url": "https://example.com"}
    asset_file.write_text(json.dumps(asset_json))

    args = runner.parse_args(
        [
            "webhook",
            "test_webhook",
            "--asset-file",
            asset_file.as_posix(),
        ]
    )
    assert args.webhook_request == WebhookRequest(
        method="GET",
        headers={},
        path_parts=["test_webhook"],
        query={},
        body=None,
        asset=Asset(base_url="https://example.com"),
        soar_base_url="https://example.com",
        soar_auth_token="",
        asset_id=1,
    )


def test_parse_args_webhook_headers(
    app_with_asset_webhook: App, tmp_asset_and_param_files
):
    """Test parsing arguments for a webhook with request headers."""
    runner = AppCliRunner(app_with_asset_webhook)

    asset_file, _ = tmp_asset_and_param_files

    # Parsing args with an invalid header should raise SystemExit
    asset_json = {"base_url": "https://example.com"}
    asset_file.write_text(json.dumps(asset_json))

    args = runner.parse_args(
        [
            "webhook",
            "test_webhook",
            "--asset-file",
            asset_file.as_posix(),
            "--header",
            "Content-Type=application/json",
            "--asset-id",
            "1",
        ]
    )

    assert args.webhook_request == WebhookRequest(
        method="GET",
        headers={"Content-Type": "application/json"},
        path_parts=["test_webhook"],
        query={},
        body=None,
        asset=Asset(base_url="https://example.com"),
        soar_base_url="https://example.com",
        soar_auth_token="",
        asset_id=1,
    )


def test_parse_args_webhook_invalid_header(
    app_with_asset_webhook: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test parsing arguments for a webhook with an invalid header."""
    runner = AppCliRunner(app_with_asset_webhook)

    asset_file, _ = tmp_asset_and_param_files

    # Parsing args with an invalid header should raise SystemExit
    asset_json = {"base_url": "https://example.com"}
    asset_file.write_text(json.dumps(asset_json))

    with pytest.raises(SystemExit):
        runner.parse_args(
            [
                "webhook",
                "test_webhook",
                "--asset-file",
                asset_file.as_posix(),
                "--header",
                "InvalidHeaderFormat",  # Missing '='
            ]
        )


def test_parse_args_webhook_flattens_params(
    app_with_asset_webhook: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test parsing arguments for a webhook."""
    runner = AppCliRunner(app_with_asset_webhook)

    asset_file, _ = tmp_asset_and_param_files
    asset_json = {"base_url": "https://example.com"}
    asset_file.write_text(json.dumps(asset_json))

    args = runner.parse_args(
        [
            "webhook",
            "test_webhook?key1=value1&key2=value2&key2=value3",
            "--asset-file",
            asset_file.as_posix(),
            "--asset-id",
            "2",
        ]
    )

    assert args.webhook_request == WebhookRequest(
        method="GET",
        headers={},
        path_parts=["test_webhook"],
        query={
            "key1": ["value1"],
            "key2": ["value2", "value3"],
        },
        body=None,
        asset=Asset(base_url="https://example.com"),
        soar_base_url="https://example.com",
        soar_auth_token="",
        asset_id=2,
    )


def test_run_action_cli(
    app_with_action: App,
    tmp_asset_and_param_files: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
):
    """Test running an action via CLI."""
    runner = AppCliRunner(app_with_action)

    _, param_file = tmp_asset_and_param_files
    param_file.write_text(json.dumps({"field1": 123}))

    # Run the action
    runner.run(["action", "test_action", "-p", param_file.as_posix()])

    # Verify the result
    captured = capsys.readouterr()
    assert "Action params: " in captured.out
    assert "Action success: " in captured.out
    assert "Result data: " in captured.out
    assert "Result summary: " in captured.out
    assert "Result message: " in captured.out
    assert "Objects successful/total: 1/1" in captured.out


def test_run_action_cli_with_encrypted_asset(
    simple_app: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test running an action with an encrypted asset via CLI."""

    class EncryptedAsset(BaseAsset):
        client_id: str
        client_secret: str = AssetField(sensitive=True)

    simple_app.asset_cls = EncryptedAsset

    credentials_sink = mock.Mock()

    @simple_app.action()
    def test_encrypted_asset(params: Params, asset: EncryptedAsset) -> ActionOutput:
        credentials_sink(
            client_id=asset.client_id,
            client_secret=asset.client_secret,
        )

    asset_file, param_file = tmp_asset_and_param_files

    asset_file.write_text(
        json.dumps(
            {"client_id": "test_client_id", "client_secret": "test_client_secret"},
        )
    )

    param_file.write_text(json.dumps({}))

    runner = AppCliRunner(simple_app)

    # Run the action
    runner.run(
        [
            "action",
            "test_encrypted_asset",
            "--asset-file",
            asset_file.as_posix(),
            "--param-file",
            param_file.as_posix(),
        ]
    )

    credentials_sink.assert_called_once_with(
        client_id="test_client_id",
        client_secret="test_client_secret",
    )


def test_run_webhook_cli(
    app_with_asset_webhook: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test running a webhook via CLI."""
    runner = AppCliRunner(app_with_asset_webhook)

    asset_file, _ = tmp_asset_and_param_files

    asset_json = {"base_url": "https://example.com"}
    asset_file.write_text(json.dumps(asset_json))

    # Run the webhook
    runner.run(["webhook", "test_webhook", "-a", asset_file.as_posix()])


def test_run_webhook_cli_base64(
    app_with_asset_webhook: App, tmp_asset_and_param_files: tuple[Path, Path]
):
    """Test running a webhook via CLI."""

    @app_with_asset_webhook.webhook("test_binary_webhook")
    def test_binary_webhook(request: WebhookRequest) -> WebhookResponse:
        return WebhookResponse.file_response(
            fd=BytesIO(b"Test content"),
            filename="test_file.txt",
            status_code=200,
            extra_headers={"X-Custom-Header": "CustomValue"},
        )

    runner = AppCliRunner(app_with_asset_webhook)

    asset_file, _ = tmp_asset_and_param_files

    asset_json = {"base_url": "https://example.com"}
    asset_file.write_text(json.dumps(asset_json))

    # Run the webhook
    runner.run(["webhook", "test_binary_webhook", "-a", asset_file.as_posix()])


def test_webhooks_with_soar_authentication(
    app_with_client_webhook: App,
    tmp_asset_and_param_files: tuple[Path, Path],
    mock_get_any_soar_call,
    mock_post_any_soar_call,
    mocker: pytest_mock.MockerFixture,
):
    """Test parsing arguments for an action that requires both asset and parameters."""
    runner = AppCliRunner(app_with_client_webhook)

    asset_file, _ = tmp_asset_and_param_files
    asset_json = {"base_url": "https://example.com"}
    asset_file.write_text(json.dumps(asset_json))

    args = runner.parse_args(
        [
            "--soar-url",
            "10.34.5.6",
            "--soar-user",
            "soar_local_admin",
            "--soar-password",
            "password",
            "webhook",
            "test_webhook",
            "--asset-file",
            asset_file.as_posix(),
            "--asset-id",
            "2",
        ]
    )

    assert args.webhook_request == WebhookRequest(
        method="GET",
        headers={},
        path_parts=["test_webhook"],
        query={},
        body=None,
        asset=Asset(base_url="https://example.com"),
        soar_base_url="10.34.5.6",
        soar_auth_token="mocked_session_id",
        asset_id=2,
    )
    mocker.patch.object(runner, "parse_args", return_value=args)
    runner.run()

    assert mock_get_any_soar_call.call_count == 3
    assert mock_post_any_soar_call.call_count == 1
