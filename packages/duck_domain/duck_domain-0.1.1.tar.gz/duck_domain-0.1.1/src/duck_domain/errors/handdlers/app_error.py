import json
from typing import Any, Dict


class AppError(Exception):
    """
    Custom exception class to represent application errors with detailed information.

    Attributes:
    - class_pointer: The class instance where the error originated.
    - title: A short, human-readable title for the error.
    - message: A detailed message describing the error.
    - details: Additional details for the error, typically a dictionary with further information.
    - code: An HTTP-like status code representing the type of error (default is 400).
    """

    def __init__(
        self,
        class_pointer: Any,
        title: str,
        message: str = "",
        details: Dict[str, Any] = {},
        code: int = 400,
    ) -> None:
        self.class_pointer = class_pointer
        self.title = title
        self.message = message
        self.details = details
        self.code = code

    @property
    def error(self) -> Dict[str, Any]:
        return {
            "class_name": self._resolve_pointer(),
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "code": self.code,
        }

    def _resolve_pointer(self) -> str:
        if isinstance(self.class_pointer, str):
            return self.class_pointer
        elif self.class_pointer is None:
            return ""
        return self.class_pointer.__class__.__name__

    def __str__(self) -> str:
        line = "-=" * 30
        try:
            error_details = json.dumps(
                self.error, ensure_ascii=False, indent=3
            )
        except TypeError:
            error_details = ""
            for k, v in self.error.items():
                error_details += f" {k}: {v}\n"

        return f"\n{line}\n\n({self.code})[{self.title.upper()}]: {self.message}\n\n{error_details}\n{line}\n"
