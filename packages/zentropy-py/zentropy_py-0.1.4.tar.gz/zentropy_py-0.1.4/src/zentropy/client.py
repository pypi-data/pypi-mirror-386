from __future__ import annotations
from typing import Optional
from .connection import Connection
from .exceptions import AuthError, ConnectionError


class Client:
    def __init__(self, host='127.0.0.1', port=6383, unix_socket=None, password=None):
        self.conn = Connection(host, port, unix_socket)
        if password:
            self.auth(password)

    def _send(self, cmd: str) -> str:
        self.conn.send(cmd + '\n')
        return self._parse_response()

    def _recv_line(self) -> bytes:
        """Read a single line (ending with newline) from socket."""
        if not self.conn.socket:
            raise ConnectionError("Not connected")
        data = b""
        while True:
            chunk = self.conn.socket.recv(1)
            if not chunk:
                raise ConnectionError("Connection closed by server")
            data += chunk
            if chunk == b'\n':
                break
        return data.rstrip(b'\r\n')

    def _parse_response(self) -> str:
        """Parse RESP-like server responses."""
        line = self._recv_line()
        if not line:
            return ''

        prefix = chr(line[0])
        rest = line[1:].decode()

        if prefix == '+':  # simple string
            return rest

        elif prefix == '-':  # error
            raise ConnectionError(f"Server error: {rest}")

        elif prefix == ':':  # integer
            return rest

        elif prefix == '$':  # bulk string
            length = int(rest)
            if length == -1:
                return 'NONE'
            data = b""
            while len(data) < length + 2:  # +2 for CRLF
                chunk = self.conn.socket.recv(length + 2 - len(data))
                if not chunk:
                    raise ConnectionError("Connection closed during bulk read")
                data += chunk
            return data[:-2].decode()  # remove CRLF

        else:
            return line.decode()

    # ------------------------
    # Public Commands
    # ------------------------

    def auth(self, password: str) -> bool:
        resp = self._send(f"AUTH {password}")
        if resp != 'OK':
            raise AuthError(f"Authentication failed: {resp}")
        return True

    def set(self, key: str, value: str) -> bool:
        return self._send(f"SET {key} '{value}'") == 'OK'

    def get(self, key: str) -> Optional[str]:
        resp = self._send(f"GET {key}")
        return None if resp == 'NONE' else resp

    def delete(self, key: str) -> bool:
        return self._send(f"DELETE {key}") == '1'

    def exists(self, key: str) -> bool:
        return self._send(f"EXISTS {key}") == '1'

    def ping(self) -> bool:
        return self._send("PING") == 'PONG'

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
