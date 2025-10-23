from collections.abc import Iterator
import pytest

import pytest_mock

from soar_sdk.app import App
from soar_sdk.params import OnPollParams
from soar_sdk.models.container import Container
from soar_sdk.models.artifact import Artifact
from soar_sdk.exceptions import ActionFailure


def test_on_poll_decoration_fails_when_used_more_than_once(app_with_action: App):
    """Test that the on_poll decorator can only be used once per app."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams, client=None) -> Iterator[dict]:
        yield {"data": "test"}

    with pytest.raises(TypeError, match=r"on_poll.+once per"):

        @app_with_action.on_poll()
        def second_on_poll(params: OnPollParams, client=None) -> Iterator[dict]:
            yield {"data": "another test"}


def test_on_poll_decoration_fails_when_not_generator(app_with_action: App):
    """Test that the on_poll decorator requires a generator function."""

    with pytest.raises(
        TypeError,
        match=r"The on_poll function must be a generator \(use 'yield'\) or return an Iterator.",
    ):

        @app_with_action.on_poll()
        def on_poll_function(params: OnPollParams, client=None):
            return {"data": "test"}  # Not yielding


def test_on_poll_function_called_with_params(
    app_with_action: App, mocker: pytest_mock.MockerFixture
):
    """Test that the on_poll function is called with parameters."""
    poll_fn = mocker.stub()

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams) -> Iterator[dict]:
        poll_fn(params)
        yield {"data": "test"}

    params = OnPollParams(
        start_time=0,
        end_time=1,
        container_count=10,
        artifact_count=100,
        container_id=1,
    )

    result = on_poll_function(params)

    poll_fn.assert_called_once_with(params)
    assert result is True


def test_on_poll_param_validation_error(app_with_action: App):
    """Test on_poll handles parameter validation errors and returns False."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams):
        yield Artifact(name="a1")

    invalid_params = "invalid"
    result = on_poll_function(invalid_params)
    assert result is False


def test_on_poll_works_with_iterator_functions(app_with_action: App):
    """Test that the on_poll decorator works with functions that return iterators."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams) -> Iterator[dict]:
        # Creating and returning an iterator
        return iter([{"data": "test artifact 1"}, {"data": "test artifact 2"}])

    params = OnPollParams(
        start_time=0,
        end_time=1,
        container_count=10,
        artifact_count=100,
    )

    result = on_poll_function(params)

    assert result is True


def test_on_poll_empty_iterator(app_with_action: App):
    """Test that the on_poll function works with empty iterators."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams) -> Iterator[dict]:
        # Empty iterator - no artifacts to yield
        return iter([])

    params = OnPollParams(
        start_time=0,
        end_time=1,
        container_id=1,
    )

    result = on_poll_function(params)

    assert result is True


def test_on_poll_raises_exception_propagates(app_with_action: App):
    """Test that exceptions raised in the on_poll function are handled and return False."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams) -> Iterator[dict]:
        raise ValueError("poll error")
        yield  # pragma: no cover

    params = OnPollParams(
        start_time=0,
        end_time=1,
        container_count=10,
        artifact_count=100,
        container_id=1,
    )

    result = on_poll_function(params)
    assert result is False


def test_on_poll_multiple_yields(app_with_action: App):
    """Test that multiple yielded items are processed by on_poll."""
    yielded = []

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams) -> Iterator[dict]:
        for i in range(3):
            yielded.append(i)
            yield {"data": i}

    params = OnPollParams(
        start_time=0,
        end_time=1,
        container_count=10,
        artifact_count=100,
        container_id=1,
    )

    result = on_poll_function(params)
    assert result is True
    assert yielded == [0, 1, 2]


def test_on_poll_yields_container_success(
    app_with_action: App, mocker: pytest_mock.MockerFixture
):
    """Test on_poll yields a Container and successfully."""

    # Mock the save_container method to return success
    save_container = mocker.patch.object(
        app_with_action.actions_manager,
        "save_container",
        return_value=(True, "Created", 42),
    )

    # Mock the save_artifacts method
    save_artifacts = mocker.patch.object(
        app_with_action.actions_manager, "save_artifacts", return_value=None
    )

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams, client=None):
        yield Container(name="c1")
        yield Artifact(name="a1")

    params = OnPollParams(start_time=0, end_time=1)
    result = on_poll_function(params, client=app_with_action.soar_client)
    assert result is True
    assert save_container.call_count == 1
    save_artifacts.assert_called()


def test_on_poll_yields_container_duplicate(
    app_with_action: App, mocker: pytest_mock.MockerFixture
):
    """Test on_poll yields a Container and handles duplicate container correctly."""
    save_container = mocker.patch.object(
        app_with_action.actions_manager,
        "save_container",
        return_value=(True, "Duplicate container found", 99),
    )
    save_artifacts = mocker.patch.object(
        app_with_action.actions_manager, "save_artifacts", return_value=None
    )

    @app_with_action.on_poll()
    def on_poll_function_dup(params: OnPollParams, client=None):
        yield Container(name="c2")
        yield Artifact(name="a2")

    params = OnPollParams(start_time=0, end_time=1)
    result = on_poll_function_dup(params, client=app_with_action.soar_client)
    assert result is True
    assert save_container.call_count == 1
    save_artifacts.assert_called()


def test_on_poll_yields_container_creation_failure(
    app_with_action: App, mocker: pytest_mock.MockerFixture
):
    """Test on_poll handles container creation failure correctly."""
    save_container = mocker.patch.object(
        app_with_action.actions_manager,
        "save_container",
        return_value=(
            False,
            "Error creating container",
            None,
        ),
    )
    save_artifacts = mocker.patch.object(
        app_with_action.actions_manager, "save_artifacts", return_value=None
    )

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams, client=None):
        yield Container(name="c3")
        yield Artifact(name="a3")  # Should be skipped because no container

    params = OnPollParams(start_time=0, end_time=1)
    result = on_poll_function(params, client=app_with_action.soar_client)
    assert result is True
    assert save_container.call_count == 1
    save_artifacts.assert_not_called()


def test_on_poll_yields_non_container_artifact(app_with_action: App):
    """Test on_poll correctly handles object that is neither Container nor Artifact."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams):
        yield 123  # Should be skipped
        yield "string"

    params = OnPollParams(start_time=0, end_time=1)
    result = on_poll_function(params)
    assert result is True


def test_on_poll_artifact_no_container(app_with_action: App):
    """Test on_poll yields an Artifact with no container and no container_id."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams):
        yield Artifact(name="a1")

    params = OnPollParams(start_time=0, end_time=1)
    result = on_poll_function(params)
    assert result is True


def test_on_poll_sets_container_id_on_artifact(
    app_with_action: App, mocker: pytest_mock.MockerFixture
):
    """Test that on_poll sets container_id on artifact if not present and container_id is available."""
    save_artifacts = mocker.patch.object(
        app_with_action.actions_manager, "save_artifacts"
    )

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams, client=None):
        artifact2 = Artifact(name="a2", container_id=999)
        yield artifact2

    params = OnPollParams(start_time=0, end_time=1)
    on_poll_function(params, client=app_with_action.soar_client)
    called_artifacts = save_artifacts.call_args_list
    saved_artifact = called_artifacts[0][0][0][0]
    assert saved_artifact["container_id"] == 999


def test_on_poll_failure(app_with_action: App):
    """Test on_poll handles ActionFailure correctly."""

    # ActionFailure
    @app_with_action.on_poll()
    def on_poll_actionfailure(params: OnPollParams):
        raise ActionFailure("failmsg")
        yield  # pragma: no cover

    params = OnPollParams(start_time=0, end_time=1)
    result = on_poll_actionfailure(params)
    assert result is False


def test_on_poll_decoration_with_meta(app_with_action: App):
    """Test that the on_poll decorator properly sets up metadata."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams) -> Iterator[dict]:
        yield {"data": "test"}

    action = app_with_action.actions_manager.get_action("on_poll")
    assert action is not None
    assert action.meta.action == "on poll"
    assert action == on_poll_function


def test_on_poll_actionmeta_dict_output_empty(app_with_action: App):
    """Test that OnPollActionMeta.dict returns output as an empty list."""

    @app_with_action.on_poll()
    def on_poll_function(params: OnPollParams):
        yield Artifact(name="a1")

    action = app_with_action.actions_manager.get_action("on_poll")
    meta_dict = action.meta.dict()
    assert "output" in meta_dict
    assert meta_dict["output"] == []
