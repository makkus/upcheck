# -*- coding: utf-8 -*-
from typing import Dict, Optional, Union


class UpcheckException(Exception):
    """Base exception class with a few helper methods to make it easy to display a good error message.

    Args:

        - *msg*: the message to display
        - *solution*: a recommendation to the user to fix or debug the issue
        - *references*: a dict with references to the issue, title/url key-value pairs.
        - *reason*: the reason for the exception
        - *parent*: a parent exception

    """

    def __init__(
        self,
        msg: Union[str, Exception, None] = None,
        solution: str = None,
        references: Dict = None,
        reason: Union[str, Exception] = None,
        parent: Exception = None,
        *args,
    ):

        if isinstance(msg, Exception) or issubclass(msg.__class__, Exception):
            if parent is None:
                parent = msg
            msg = str(msg)

        if msg is None:
            msg = "unspecified internal error"

        super(UpcheckException, self).__init__(msg, *args)
        self.msg = msg
        self.solution = solution
        self._reason = reason
        self.references = references
        self.parent = parent

    @property
    def reason(self) -> Optional[str]:

        if not self._reason:
            return None

        if isinstance(self._reason, str):
            return self._reason
        else:
            return str(self._reason)

    @property
    def message(self):

        msg = self.msg
        if not msg.endswith("."):
            msg = msg + "."

        msg = msg + "\n"

        if self.reason:
            msg = msg + "\n  Reason: {}".format(self.reason)
        elif self.parent:
            msg_parent = str(self.parent)
            msg = msg + f"\n  Parent error: {msg_parent}"
        if self.solution:
            msg = msg + "\n  Solution: {}".format(self.solution)
        if self.references:
            if len(self.references) == 1:
                url = self.references[list(self.references.keys())[0]]
                msg = msg + "\n  Reference: {}".format(url)
            else:
                msg = msg + "\n  References\n"
                for k, v in self.references.items():
                    msg = msg + "\n    {}: {}".format(k, v)

        return msg.rstrip()

    @property
    def message_short(self):

        msg = self.msg
        if not msg.endswith("."):
            msg = msg + "."

        if self.reason:
            reason = self.reason
            if not reason.endswith("."):
                reason = reason + "."
            msg = f"{msg} {reason}"
        elif self.parent:
            reason = repr(self.parent)
            if not reason.endswith("."):
                reason = reason + "."
            msg = f"{msg} {reason}"
        if self.solution:
            solution = self.solution
            if not solution.endswith("."):
                solution = solution + "."
            msg = f"{msg} {solution}"

        msg = msg.replace("\n", " ")

        return msg

    def __str__(self):

        return self.message_short

    def __repr__(self):
        return self.message


def ensure_upcheck_exception(exc) -> UpcheckException:

    if isinstance(exc, UpcheckException) or issubclass(exc.__class__, UpcheckException):
        return exc

    return UpcheckException(msg=exc)
