# -*- coding: utf-8 -*-
"""Message class."""
from abc import ABC, abstractmethod
from typing import List, Dict, Union, Tuple, Any, Optional
import re
import datetime
import json
import copy
from warnings import warn
from .params import MEMOR_VERSION
from .params import RenderFormat
from .params import Role
from .params import XML_PATTERN
from .tokens_estimator import TokensEstimator
from .params import INVALID_ROLE_MESSAGE, MESSAGE_SIZE_WARNING
from .errors import MemorValidationError
from .functions import get_time_utc, generate_message_id
from .functions import _validate_string, _validate_pos_int
from .functions import _validate_pos_float, _validate_path


class Message(ABC):
    """Message class."""

    def __init__(self) -> None:
        """Message initiator."""
        self._message = ""
        self._warnings = dict()
        self._tokens = None
        self._role = Role.DEFAULT
        self._date_created = get_time_utc()
        self._mark_modified()
        self._memor_version = MEMOR_VERSION
        self._id = None

    def _mark_modified(self) -> None:
        """Mark modification."""
        self._date_modified = get_time_utc()

    def __str__(self) -> str:
        """Return string representation of Message."""
        return self.render(render_format=RenderFormat.STRING, show_warning=False)

    def __len__(self) -> int:
        """Return the length of the Message."""
        try:
            return len(self.render(render_format=RenderFormat.STRING, show_warning=False))
        except Exception:
            return 0

    def __copy__(self) -> "Message":
        """
        Return a copy of the Message.

        :return: a copy of Message
        """
        _class = self.__class__
        result = _class.__new__(_class)
        result.__dict__.update(self.__dict__)
        result.regenerate_id()
        return result

    def copy(self) -> "Message":
        """
        Return a copy of the Message.

        :return: a copy of Message
        """
        return self.__copy__()

    def update_message(self, message: str) -> None:
        """
        Update the message.

        :param message: message
        """
        _validate_string(message, "message")
        self._message = message
        self._mark_modified()

    def update_role(self, role: Role) -> None:
        """
        Update the role.

        :param role: role
        """
        if not isinstance(role, Role):
            raise MemorValidationError(INVALID_ROLE_MESSAGE)
        self._role = role
        self._mark_modified()

    def update_tokens(self, tokens: Optional[int]) -> None:
        """
        Update the tokens.

        :param tokens: tokens
        """
        if tokens is None or _validate_pos_int(tokens, "tokens"):
            self._tokens = tokens
            self._mark_modified()

    @abstractmethod
    def save(self, file_path: str) -> Dict[str, Any]:
        """
        Save method.

        :param file_path: message file path
        """
        pass  # pragma: no cover

    def load(self, file_path: str) -> None:
        """
        Load method.

        :param file_path: message file path
        """
        _validate_path(file_path)
        with open(file_path, "r") as file:
            self.from_json(file.read())

    @staticmethod
    @abstractmethod
    def _validate_extract_json(json_object: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate and extract JSON object.

        :param json_object: JSON object
        """
        pass  # pragma: no cover

    @abstractmethod
    def from_json(self, json_object: Union[str, Dict[str, Any]]) -> None:
        """
        Load attributes from the JSON object.

        :param json_object: JSON object
        """
        pass  # pragma: no cover

    @abstractmethod
    def to_json(self) -> Dict[str, Any]:
        """Convert the message to a JSON object."""
        pass  # pragma: no cover

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        pass  # pragma: no cover

    def get_size(self) -> int:
        """Get the size of the message in bytes."""
        json_str = json.dumps(self.to_json())
        return len(json_str.encode())

    def regenerate_id(self) -> None:
        """Regenerate ID."""
        new_id = self._id
        while new_id == self.id:
            new_id = generate_message_id()
        self._id = new_id

    @property
    def message(self) -> str:
        """Get the message."""
        return self._message

    @property
    def role(self) -> Role:
        """Get the role."""
        return self._role

    @property
    def tokens(self) -> int:
        """Get the tokens."""
        return self._tokens

    @property
    def date_created(self) -> datetime.datetime:
        """Get the creation date."""
        return self._date_created

    @property
    def date_modified(self) -> datetime.datetime:
        """Get the message object modification date."""
        return self._date_modified

    @property
    def id(self) -> str:
        """Get the message ID."""
        return self._id

    @property
    def size(self) -> int:
        """Get the size of the message in bytes."""
        return self.get_size()

    @property
    def warnings(self) -> Dict[str, Dict[str, Union[float, bool]]]:
        """Get the message warnings."""
        return copy.deepcopy(self._warnings)

    @abstractmethod
    def render(self, render_format: RenderFormat = RenderFormat.DEFAULT,
               show_warning: bool = True) -> Union[str, Dict[str, Any], List[Tuple[str, Any]]]:
        """
        Render method.

        :param render_format: render format
        :param show_warning: show warning flag
        """
        pass  # pragma: no cover

    def check_render(self) -> bool:
        """Check render."""
        try:
            _ = self.render(show_warning=False)
            return True
        except Exception:
            return False

    def estimate_tokens(self, method: TokensEstimator = TokensEstimator.DEFAULT) -> int:
        """
        Estimate the number of tokens in the message.

        :param method: token estimator method
        """
        return method(self.render(render_format=RenderFormat.STRING, show_warning=False))

    def contains_xml(self) -> bool:
        """Check if the message contains any XML tags."""
        return bool(re.search(XML_PATTERN, self.render(render_format=RenderFormat.STRING, show_warning=False)))

    def _handle_size_warning(self) -> None:
        """Size warning handler."""
        size_warning = self._warnings.get("size", {})
        if size_warning.get("enable", False):
            message_size = self.get_size()
            size_threshold = size_warning.get("threshold", None)
            if isinstance(size_threshold, (float, int)):
                if message_size > size_threshold:
                    warn(
                        MESSAGE_SIZE_WARNING.format(
                            message_id=self.id,
                            current_size=message_size,
                            threshold=size_threshold),
                        RuntimeWarning)

    def set_size_warning(self, threshold: Union[float, int]) -> None:
        """
        Set the size warning.

        :param threshold: size threshold
        """
        _validate_pos_float(threshold, "threshold")
        self._warnings["size"] = dict()
        self._warnings["size"]["enable"] = True
        self._warnings["size"]["threshold"] = threshold
        self._mark_modified()

    def reset_size_warning(self) -> None:
        """Reset the size warning."""
        self._warnings["size"] = dict()
        self._warnings["size"]["enable"] = False
        self._warnings["size"]["threshold"] = 0
        self._mark_modified()
