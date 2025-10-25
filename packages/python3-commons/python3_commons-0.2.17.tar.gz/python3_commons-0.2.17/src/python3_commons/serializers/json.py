import base64
import dataclasses
import json
from datetime import date, datetime
from decimal import Decimal
from socket import socket
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o) -> Any:
        try:
            return super().default(o)
        except TypeError:
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            if isinstance(o, bytes):
                return base64.b64encode(o).decode('ascii')
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            if isinstance(o, (Decimal, socket, type, Exception)):
                return str(o)

        return type(o).__name__
