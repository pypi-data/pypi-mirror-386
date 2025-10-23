try:
    from phantom.action_result import ActionResult

    _soar_is_available = True
except ImportError:
    _soar_is_available = False

from typing import Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING or not _soar_is_available:

    class ActionResult:  # type: ignore[no-redef]
        def __init__(self, param: Optional[dict] = None) -> None:
            self.status = False
            self.message = ""
            self.summary: dict[str, Any] = {}

            if param is None:
                self.param = {}
            elif type(param) is dict:
                self.param = param
            else:
                raise TypeError("param must be dict")

        def set_status(
            self,
            status_code: Union[bool, int],
            _status_message: str = "",
            _exception: Optional[Exception] = None,
        ) -> bool:
            self.status = bool(status_code)
            self.message = _status_message
            return self.status

        def get_status(self) -> bool:
            return self.status

        def get_param(self) -> dict:
            return self.param

        def add_data(self, data: dict) -> None:
            if not hasattr(self, "_data"):
                self._data = []
            self._data.append(data)

        def get_data(self) -> list[dict]:
            return getattr(self, "_data", [])

        def set_summary(self, summary: dict) -> None:
            self.summary = summary

        def get_summary(self) -> dict:
            return self.summary

        def get_message(self) -> str:
            return self.message


__all__ = ["ActionResult"]
