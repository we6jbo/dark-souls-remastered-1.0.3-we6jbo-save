#!/usr/bin/env python3
"""BBS.py-side bridge for the headless Local Talk service on 127.0.0.1:32512."""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

HOST = '127.0.0.1'
PORT = 32512
LOCALCHAT = Path('/home/we6jbo/Darksouls-game/KVS6/localchat.py')


class LocalTalkBridge:
    def __init__(self, host=HOST, port=PORT, script=LOCALCHAT):
        self.host = host
        self.port = int(port)
        self.script = Path(script)

    def _exchange(self, command, timeout=3.0):
        with socket.create_connection((self.host, self.port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            f = sock.makefile('rwb', buffering=0)
            # localchat.py sends a one-line greeting for every connection.
            greeting = f.readline().decode('utf-8', 'replace').rstrip('\r\n')
            if greeting != 'LOCALCHAT READY':
                raise RuntimeError(f'Unexpected Local Talk greeting: {greeting!r}')
            f.write((command + '\n').encode('utf-8'))
            if command.upper() == 'HEALTH':
                rows = []
                while True:
                    line = f.readline().decode('utf-8', 'replace').rstrip('\r\n')
                    if not line or line == '.':
                        break
                    rows.append(line)
                return '\n'.join(rows)
            return f.readline().decode('utf-8', 'replace').rstrip('\r\n')

    def is_running(self):
        try:
            return self._exchange('PING', timeout=0.75) == 'PONG'
        except OSError:
            return False
        except Exception:
            return False

    def ensure_running(self, startup_timeout=12.0):
        """Start localchat.py only when port 32512 is not already responding."""
        if self.is_running():
            return True
        if not self.script.exists():
            raise FileNotFoundError(self.script)
        subprocess.Popen(
            [sys.executable, str(self.script)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            cwd=str(self.script.parent),
        )
        deadline = time.monotonic() + float(startup_timeout)
        while time.monotonic() < deadline:
            if self.is_running():
                return True
            time.sleep(0.2)
        return False

    def status(self):
        return self._exchange('STATUS')

    def health(self):
        text = self._exchange('HEALTH')
        result = {}
        for line in text.splitlines():
            if ' ' in line:
                key, value = line.split(' ', 1)
                result[key.lower()] = value
        return result

    def send(self, message):
        message = str(message).replace('\r', ' ').replace('\n', ' ').strip()
        if not message:
            return 'ERROR empty message'
        return self._exchange('SEND ' + message, timeout=5.0)

    def start_rotation(self):
        return self._exchange('START')

    def stop_rotation(self):
        return self._exchange('STOP')

    def shutdown(self):
        try:
            return self._exchange('SHUTDOWN')
        except OSError:
            return 'OK already stopped'


if __name__ == '__main__':
    bridge = LocalTalkBridge()
    if not bridge.ensure_running():
        raise SystemExit('Local Talk did not start; inspect /home/we6jbo/Darksouls-game/KVS6/errors.json')
    print(bridge.status())
