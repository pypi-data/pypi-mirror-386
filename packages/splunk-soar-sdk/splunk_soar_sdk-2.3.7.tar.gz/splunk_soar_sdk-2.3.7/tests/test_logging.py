from unittest import mock
import pytest
import pytest_mock

from soar_sdk.logging import (
    getLogger,
    debug,
    error,
    info,
    progress,
    critical,
    warning,
    SOARHandler,
    PhantomLogger,
)
from soar_sdk.colors import ANSIColor
import soar_sdk.logging
from soar_sdk.shims.phantom.ph_ipc import ph_ipc


@pytest.fixture
def ph_ipc_mock(mocker: pytest_mock.MockerFixture) -> dict[str, mock.Mock]:
    mocks = mocker.patch.multiple(
        ph_ipc,
        sendstatus=mock.DEFAULT,
        debugprint=mock.DEFAULT,
        errorprint=mock.DEFAULT,
    )
    return mocks


def test_root_logger(ph_ipc_mock: dict[str, mock.Mock]):
    import logging as python_logger

    logger = python_logger.getLogger()
    logger.warning("This is an info message from the test_logging module.")
    ph_ipc_mock["debugprint"].assert_called()


def test_logging(ph_ipc_mock: dict[str, mock.Mock]):
    logger = getLogger()

    msg = "This is an info message from the test_logging module."
    logger.info(msg)
    ph_ipc_mock["sendstatus"].assert_called_with(
        None,
        1,
        f"\x1b[0m{msg}\x1b[0m",
        True,
    )

    msg = "This is a debug message from the test_logging module."
    logger.debug(msg)
    ph_ipc_mock["debugprint"].assert_called_with(None, f"\x1b[2m{msg}\x1b[0m", 2)

    msg = "This is a critical message from the test_logging module."
    logger.critical(msg)
    ph_ipc_mock["errorprint"].assert_called_with(
        None,
        f"\x1b[1;4;31m{msg}\x1b[0m",
        2,
    )

    msg = "This is a progress message from the test_logging module."
    logger.progress(msg)
    ph_ipc_mock["sendstatus"].assert_called_with(
        None,
        1,
        f"{msg}\x1b[0m",
        False,
    )

    msg = "This is a warning message from the test_logging module."
    logger.warning(msg)
    ph_ipc_mock["debugprint"].assert_called_with(
        None,
        f"\x1b[33m{msg}\x1b[0m",
        2,
    )

    msg = "This is an error message from the test_logging module."
    logger.error(msg)
    ph_ipc_mock["errorprint"].assert_called_with(
        None,
        f"\x1b[1;31m{msg}\x1b[0m",
        2,
    )


def test_standalone_logging(ph_ipc_mock: dict[str, mock.Mock]):
    msg = "This is an info message from the test_logging module."
    info(msg)
    ph_ipc_mock["sendstatus"].assert_called_with(
        None,
        1,
        f"\x1b[0m{msg}\x1b[0m",
        True,
    )

    msg = "This is a debug message from the test_logging module."
    debug(msg)
    ph_ipc_mock["debugprint"].assert_called_with(None, f"\x1b[2m{msg}\x1b[0m", 2)

    msg = "This is a critical message from the test_logging module."
    critical(msg)
    ph_ipc_mock["errorprint"].assert_called_with(
        None,
        f"\x1b[1;4;31m{msg}\x1b[0m",
        2,
    )

    msg = "This is a progress message from the test_logging module."
    progress(msg)
    ph_ipc_mock["sendstatus"].assert_called_with(
        None,
        1,
        f"{msg}\x1b[0m",
        False,
    )

    msg = "This is a warning message from the test_logging module."
    warning(msg)
    ph_ipc_mock["debugprint"].assert_called_with(
        None,
        f"\x1b[33m{msg}\x1b[0m",
        2,
    )

    msg = "This is an error message from the test_logging module."
    error(msg)
    ph_ipc_mock["errorprint"].assert_called_with(
        None,
        f"\x1b[1;31m{msg}\x1b[0m",
        2,
    )


def test_is_new_soar_with_version_7_0_0(
    ph_ipc_mock: dict[str, mock.Mock], mocker: pytest_mock.MockerFixture
):
    mocker.patch("soar_sdk.logging.get_product_version", return_value="7.0.0")
    logger = getLogger()

    logger.progress("Test progress message for SOAR 7.0.0")
    ph_ipc_mock["sendstatus"].assert_called_with(
        ph_ipc.PH_STATUS_PROGRESS,
        "Test progress message for SOAR 7.0.0\x1b[0m",
        False,
    )

    logger.debug("Test debug message for SOAR 7.0.0")
    ph_ipc_mock["debugprint"].assert_called_with(
        "\x1b[2mTest debug message for SOAR 7.0.0\x1b[0m"
    )

    logger.critical("Test critical message for SOAR 7.0.0")
    ph_ipc_mock["errorprint"].assert_called_with(
        "\x1b[1;4;31mTest critical message for SOAR 7.0.0\x1b[0m"
    )

    logger.info("Test info message for SOAR 7.0.0")
    ph_ipc_mock["sendstatus"].assert_called_with(
        ph_ipc.PH_STATUS_PROGRESS,
        "\x1b[0mTest info message for SOAR 7.0.0\x1b[0m",
        True,
    )


def test_logging_soar_not_available(
    ph_ipc_mock: dict[str, mock.Mock], mocker: pytest_mock.MockerFixture
):
    mocker.patch.object(soar_sdk.logging, "is_soar_available", return_value=True)
    logger = PhantomLogger()
    logger.info("This is an info message from the test_logging module.")
    ph_ipc_mock["sendstatus"].assert_called_with(
        None, 1, "This is an info message from the test_logging module.", True
    )


def test_progress_not_called(ph_ipc_mock: dict[str, mock.Mock]):
    logger = getLogger()
    logger.setLevel(50)
    logger.progress("Progress message not called because log level is too high")
    ph_ipc_mock["sendstatus"].assert_not_called()


def test_connector_error_caught(
    ph_ipc_mock: dict[str, mock.Mock], mocker: pytest_mock.MockerFixture
):
    ph_ipc_mock["errorprint"].side_effect = Exception("Simulated error")

    logger = getLogger()
    handleError = mocker.patch.object(logger.handler, "handleError")
    logger.critical("This is an error message from the test_logging module.")
    handleError.assert_called_once()


def test_non_existant_log_level(mocker: pytest_mock.MockerFixture):
    logger = getLogger()
    handleError = mocker.patch.object(logger.handler, "handleError")
    logger.log(999, "This is a test message with an invalid log level.")
    handleError.assert_called_once()


def test_remove_handler_allowed():
    import logging as python_logger

    logger = getLogger()
    handler = python_logger.StreamHandler()
    logger.addHandler(handler)
    assert handler in logger.handlers
    logger.removeHandler(handler)
    assert handler not in logger.handlers


def test_remove_soar_handler_not_allowed():
    logger = getLogger()
    handler = SOARHandler()

    with pytest.raises(ValueError, match="Removing the SOARHandler is not allowed."):
        logger.removeHandler(handler)


def test_getattr_non_existant_color():
    """Tests __getattr__ returns the correct color when color is enabled."""
    color = ANSIColor(False)
    with pytest.raises(AttributeError):
        color.Random  # noqa: B018

    assert color._get_color("BLUE") == ""
