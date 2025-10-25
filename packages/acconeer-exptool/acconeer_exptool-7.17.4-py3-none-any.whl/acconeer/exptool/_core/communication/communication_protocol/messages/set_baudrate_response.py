# Copyright (c) Acconeer AB, 2022-2023
# All rights reserved
from __future__ import annotations

import typing as t

import attrs
import typing_extensions as te

from .message import Message, ParseError


class SetBaudrateResponseHeader(te.TypedDict):
    status: te.Literal["ok"]
    message: te.Literal["set baudrate"]


@attrs.frozen
class SetBaudrateResponse(Message):
    @classmethod
    def parse(cls, header: dict[str, t.Any], payload: bytes) -> SetBaudrateResponse:
        t.cast(SetBaudrateResponseHeader, header)

        if header.get("status") == "ok" and header.get("message") == "set baudrate":
            return cls()
        else:
            raise ParseError
