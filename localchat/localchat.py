#!/usr/bin/env python3
"""greyircclient - accessible rotating IRC client."""
from __future__ import annotations

import importlib.util
import json
import re
import socket
import socketserver
import signal
import ssl
import threading
import time
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
import random
from pathlib import Path

ROOT = Path('/home/we6jbo/Darksouls-game/KVS6')
DATA = ROOT / 'ZU.json'
EXTDIR = ROOT / 'ada'
ADA_SETTINGS = ROOT / 'ada-settings.json'
LOCAL_TALK = ROOT / 'localtalk.json'
ERRORS = ROOT / 'errors.json'
STATE_FILE = ROOT / 'localchat-state.json'
CONTROL_HOST = '127.0.0.1'
CONTROL_PORT = 32512
CLIENT_NAME = 'greyircclient'
BASE_NICK = 'we6jboIRC'
UNDERNET_NICK = 'we6jbo'
ACCOUNT_INFO = Path('/home/we6jbo/.w3Whw/account-info.json')

def load_account_info():
    try:
        obj = json.loads(ACCOUNT_INFO.read_text(encoding='utf-8'))
        if not isinstance(obj, dict):
            raise ValueError('account-info.json must contain a JSON object')
        return obj
    except Exception:
        return {}

ACCOUNT = load_account_info()
EMAIL = str(ACCOUNT.get('nickserv_email', ''))
PASSWORD = str(ACCOUNT.get('nickserv_password', ''))
UNDERNET_PASSWORD = str(ACCOUNT.get('undernet_password', ''))
RIZON_AUTO_SERVICE_DELAY = 30
RUNNING = ROOT / 'running.txt'
TEMP_START = datetime(2026, 8, 15, 17, 41)
TEMP_END = datetime(2026, 8, 15, 18, 41)
TEMP_REMARK = ('Temporary Aug 15 17:41-18:41 traversal uses exactly one candidate channel per server '
               'and a standalone 30-second successful-join dwell. This 30-second rule is unrelated to '
               'and must not modify or be interpreted as part of the normal two-minute chatter rule '
               'or the normal 30-second ban/kick cooldown rule.')
IDENTITY_WAIT_LIMIT = 300
REGISTRATION_WAIT_LIMIT = 120
DALNET_REGISTRATION_WAIT_LIMIT = 300
TLS_BAD_RECORD_RETRIES = 1
CONNECTION_HANDOFF_GRACE = 3.0

# TLS is used where the network publicly documents a TLS endpoint. QuakeNet
# and Undernet are configured conservatively on their documented plain ports.
NETWORKS = [
    {'name': 'EsperNet',    'host': 'irc.esper.net',    'port': 6697, 'tls': True},
    {'name': 'DALnet',      'host': 'irc.dal.net',      'port': 6697, 'tls': True},
    {'name': 'Libera.Chat', 'host': 'irc.libera.chat',  'port': 6697, 'tls': True},
    {'name': 'Snoonet',     'host': 'irc.snoonet.org',  'port': 6697, 'tls': True},
    {'name': 'OFTC',        'host': 'irc.oftc.net',      'port': 6697, 'tls': True},
    {'name': 'Rizon',       'host': 'irc.rizon.net',     'port': 6697, 'tls': True},
    {'name': 'QuakeNet',    'host': 'irc.quakenet.org',  'port': 6667, 'tls': False},
    {'name': 'EFnet',       'host': 'irc.efnet.org',     'port': 6697, 'tls': True},
    {'name': 'Undernet',    'host': 'irc.undernet.org',  'port': 6667, 'tls': False},
]

OFFICIAL_WORDS = {
    'help', 'support', 'staff', 'opers', 'operator', 'services', 'service',
    'network', 'welcome', 'rules', 'abuse', 'security', 'debian', 'ubuntu',
    'libera', 'snoonet', 'esper', 'dalnet', 'oftc', 'rizon', 'quakenet',
    'efnet', 'undernet', 'freenode', 'irc', 'linux', 'python', 'gentoo',
}
BOT_RE = re.compile(r'(?:bot|serv|service|relay|bridge|logger|log)$', re.I)
BAN_RE = re.compile(r'\b(?:ban(?:ned)?|g-?line|k-?line|z-?line|akill)\b', re.I)
KICK_RE = re.compile(r'\bkick(?:ed)?\b', re.I)
NS_RE = re.compile(r'nickserv', re.I)
REGISTER_RE = re.compile(r'(?i)(?:/msg\s+nickserv\s+)?register\s+[^\r\n]+')
IDENTIFY_RE = re.compile(r'(?i)(?:/msg\s+nickserv\s+)?identify\s+[^\r\n]+')


def now():
    return datetime.now(timezone.utc).isoformat()


def redact_secrets(text):
    out = str(text)
    for secret in (PASSWORD, UNDERNET_PASSWORD):
        if secret:
            out = out.replace(secret, '<password>')
    return out


def blank_data():
    return {
        'client': CLIENT_NAME,
        'version_title': 'localtalk-auto',
        'nickname': BASE_NICK,
        'message_command': '/msg #target message',
        'networks': {},
        'events': [],
    }


def load_data():
    try:
        obj = json.loads(DATA.read_text(encoding='utf-8'))
        if isinstance(obj, dict):
            obj.pop('email', None)
            obj.pop('password', None)
            obj.pop('nickserv_password', None)
            obj.pop('undernet_password', None)
            return obj
    except Exception:
        pass
    return blank_data()


def save_data(obj):
    obj.pop('email', None)
    obj.pop('password', None)
    obj.pop('nickserv_password', None)
    obj.pop('undernet_password', None)
    DATA.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')


@dataclass
class State:
    net: dict | None = None
    nick: str = BASE_NICK
    sock: socket.socket | None = None
    stop: threading.Event = field(default_factory=threading.Event)
    registered: threading.Event = field(default_factory=threading.Event)
    authenticated: threading.Event = field(default_factory=threading.Event)
    list_done: threading.Event = field(default_factory=threading.Event)
    list_rows: list = field(default_factory=list)
    current_channel: str | None = None
    chatter: list = field(default_factory=list)
    kicked: threading.Event = field(default_factory=threading.Event)
    banned: threading.Event = field(default_factory=threading.Event)
    server_banned: threading.Event = field(default_factory=threading.Event)
    joined: threading.Event = field(default_factory=threading.Event)
    join_failed: threading.Event = field(default_factory=threading.Event)
    identity_attention: threading.Event = field(default_factory=threading.Event)
    connection_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    connection_failed: threading.Event = field(default_factory=threading.Event)
    tls_bad_record: threading.Event = field(default_factory=threading.Event)
    read_error: str | None = None
    reader_thread: threading.Thread | None = None
    talking: bool = False
    protected_until: float = 0.0
    protected_seconds: int = 0
    service_timer_started: bool = False
    last_human_activity: float = 0.0
    human_messages_seen: int = 0


class InstanceGuard:
    """Newest Wi.py owns running.txt; older live instances exit."""
    def __init__(self, emit):
        self.emit = emit
        self.instance_id = uuid.uuid4().hex
        self.pid = os.getpid()
        self.started = now()
        self.stop = threading.Event()
        ROOT.mkdir(parents=True, exist_ok=True)
        self.claim()

    def payload(self):
        return {
            'client': CLIENT_NAME,
            'pid': self.pid,
            'instance_id': self.instance_id,
            'started': self.started,
            'updated': now(),
        }

    def claim(self):
        tmp = RUNNING.with_suffix('.txt.tmp')
        tmp.write_text(json.dumps(self.payload(), indent=2), encoding='utf-8')
        tmp.replace(RUNNING)

    def owns_marker(self):
        try:
            obj = json.loads(RUNNING.read_text(encoding='utf-8'))
            return obj.get('instance_id') == self.instance_id
        except Exception:
            return False

    def watch(self, on_replaced):
        def worker():
            while not self.stop.wait(1.0):
                if not self.owns_marker():
                    self.emit('[instance] A newer Wi.py is now running; this older instance is closing.')
                    on_replaced()
                    return
        threading.Thread(target=worker, daemon=True).start()

    def release(self):
        self.stop.set()
        # Never delete a newer instance's marker.
        if self.owns_marker():
            try:
                RUNNING.unlink()
            except FileNotFoundError:
                pass


class Client:
    def __init__(self, emit, diagnostic=None):
        self.emit = emit
        self.diagnostic = diagnostic
        self.state = State()
        self.data = load_data()
        save_data(self.data)
        self.lock = threading.Lock()
        self.extensions = []
        self.ada_settings = self.load_ada_settings()
        self.load_extensions()
        self.manual_net_index = -1
        self.manual_rows = []
        self.manual_row_index = 0
        self.manual_successes = 0
        self.manual_busy = threading.Lock()
        self.manual_cooldown_until = 0.0
        self.temp_30_enabled = False
        self.temp_traversal_running = False
        self.global_stop = threading.Event()
        self.user_resume_event = threading.Event()
        self.user_resume_event.set()
        self.user_suspended = False
        self.pending_outgoing = None
        self.presence_lock = threading.Lock()
        self.presence_challenge_started = None
        self.presence_next_check = None
        self.last_user_input = 0.0
        self.rotation_thread = None
        self.presence_thread = threading.Thread(target=self._presence_watchdog, daemon=True, name='user-presence-watchdog')
        self.presence_thread.start()

    def log(self, text):
        self.emit(text)

    def set_talking(self, active, channel=None):
        state = self.state
        active = bool(active)
        if state.talking == active:
            return
        state.talking = active
        status_context = {'status': 'start' if active else 'stop',
                          'network': state.net['name'] if state.net else None,
                          'channel': channel or state.current_channel}
        if active:
            self.log('[Start talking]')
            self.persist({'type': 'talk_status', **status_context})
            self._arm_presence_challenge_if_due()
            self._flush_pending_outgoing()
        else:
            self.log('[Stop talking]')
            self.persist({'type': 'talk_status', **status_context})
            with self.presence_lock:
                # No human conversation means there is nothing for the user to
                # respond to, so a currently-running presence challenge is cancelled.
                self.presence_challenge_started = None
        self.call_ada_hook('on_status', status_context)

    def _presence_interval(self):
        lo, hi = self.ada_settings.get('user_presence_recheck_seconds', [300, 600])
        return random.uniform(float(lo), float(hi))

    def _arm_presence_challenge_if_due(self):
        if self.user_suspended or not self.state.talking:
            return
        tick = time.monotonic()
        with self.presence_lock:
            if self.presence_challenge_started is not None:
                return
            if self.presence_next_check is not None and tick < self.presence_next_check:
                return
            self.presence_challenge_started = tick
            self.presence_next_check = None
        seconds = int(self.ada_settings.get('user_presence_response_seconds', 120))
        self.persist({'type': 'user_presence_window_started', 'seconds': seconds,
                      'network': self.state.net.get('name') if self.state.net else None,
                      'channel': self.state.current_channel})

    def note_user_input(self):
        tick = time.monotonic()
        was_suspended = self.user_suspended
        with self.presence_lock:
            self.last_user_input = tick
            self.presence_challenge_started = None
            self.presence_next_check = tick + self._presence_interval()
        if was_suspended:
            self.user_suspended = False
            self.user_resume_event.set()
            # While asleep, [Start talking] means the message box is ready to wake
            # the client. As soon as the user sends something, return to
            # [Stop talking] while IRC reconnects and searches for live chatter.
            self.log('[Stop talking]')
            self.log('[presence] User input detected; automatic IRC traversal may resume.')
            self.persist({'type': 'user_presence_resumed', 'status_after_wake': 'stop'})
        # A genuine human PRIVMSG in the active channel is still what changes the
        # connected/searching client from [Stop talking] to [Start talking].

    def suspend_for_user_idle(self):
        if self.user_suspended:
            return
        self.user_suspended = True
        self.user_resume_event.clear()
        self.set_talking(False, self.state.current_channel)
        self.log('[presence] No user message during the 2-minute response window; disconnecting and pausing IRC traversal.')
        self.persist({'type': 'user_presence_suspended', 'reason': 'no_user_message_within_response_window'})
        # Disconnecting wakes the current channel/network worker; rotate() then
        # blocks on user_resume_event before opening another server connection.
        self.disconnect()
        # In the fully idle/disconnected state, Start talking means "you may type
        # now". Sending a message wakes traversal and immediately changes the GUI
        # back to Stop talking until real channel activity is found. This does not
        # set state.talking and therefore cannot arm the channel/presence timers.
        self.log('[Start talking]')
        self.persist({'type': 'idle_input_ready', 'status': 'start',
                      'meaning': 'disconnected_waiting_for_user_message'})

    def _presence_watchdog(self):
        while not self.global_stop.is_set():
            time.sleep(0.5)
            if self.user_suspended or not self.state.talking:
                continue
            self._arm_presence_challenge_if_due()
            response = float(self.ada_settings.get('user_presence_response_seconds', 120))
            with self.presence_lock:
                started = self.presence_challenge_started
                last_input = self.last_user_input
            if started is not None and last_input < started and time.monotonic() - started >= response:
                self.suspend_for_user_idle()

    def _wait_for_user_resume(self):
        while not self.global_stop.is_set():
            if self.user_resume_event.wait(0.5):
                return True
        return False

    def _flush_pending_outgoing(self):
        if not self.state.talking or not self.state.current_channel:
            return
        with self.presence_lock:
            message = self.pending_outgoing
            self.pending_outgoing = None
        if message:
            self.send_message(self.state.current_channel, message, count_as_user_input=False)

    def protection_remaining(self):
        return max(0.0, self.state.protected_until - time.monotonic())

    def apply_channel_protection(self, seconds, channel, raw):
        seconds = max(1, int(seconds))
        self.state.protected_seconds = seconds
        self.state.protected_until = max(self.state.protected_until, time.monotonic() + seconds)
        self.set_talking(False, channel)
        self.log(f'[protected] {channel}: Stop talking for {seconds} seconds; traversal and channel-send timers are paused.')
        self.persist({'type': 'channel_protection_wait', 'network': self.state.net['name'] if self.state.net else None,
                      'channel': channel, 'seconds': seconds, 'raw': raw})

    def wait_action_gap(self, action, channel=None):
        key = 'part_delay_seconds' if action.upper() == 'PART' else 'join_delay_seconds'
        lo, hi = self.ada_settings.get(key, [5.0, 7.0])
        delay = random.uniform(float(lo), float(hi))
        label = f' {channel}' if channel else ''
        self.log(f'[channel] waiting {delay:.1f}s before {action}{label}')
        end = time.monotonic() + delay
        while time.monotonic() < end:
            if self.state.connection_failed.is_set() or self.state.stop.is_set():
                return False
            time.sleep(0.1)
        return True

    def persist(self, event=None):
        event_context = None
        with self.lock:
            if event:
                event_context = {'time': now(), **event}
                self.data.setdefault('events', []).append(event_context)
                self.data['events'] = self.data['events'][-500:]
            save_data(self.data)
        if event_context is not None:
            if self.diagnostic is not None:
                try:
                    self.diagnostic(dict(event_context))
                except Exception:
                    pass
            if hasattr(self, 'extensions'):
                self.call_ada_hook('on_event', dict(event_context))

    def netrec(self):
        name = self.state.net['name'] if self.state.net else 'unknown'
        return self.data.setdefault('networks', {}).setdefault(name, {
            'server': None,
            'nickserv_detected': False,
            'nickserv_register_help': [],
            'nickserv_identify_help': [],
            'register_command': None,
            'identify_command': None,
            'successful_channels': [],
            'ban_events': [],
            'kick_events': [],
            'message_command': '/msg #target message',
        })

    def load_ada_settings(self):
        defaults = {
            'enabled': True,
            'status_only_gui': True,
            'human_activity_timeout_seconds': 120,
            'join_delay_seconds': [5.0, 7.0],
            'part_delay_seconds': [5.0, 7.0],
            'send_delay_seconds_per_character': [2.3, 2.7],
            'localtalk_max_messages': 11,
            'user_presence_response_seconds': 120,
            'user_presence_recheck_seconds': [300, 600],
            'plugin_directory': str(EXTDIR),
        }
        try:
            obj = json.loads(ADA_SETTINGS.read_text(encoding='utf-8'))
            if isinstance(obj, dict):
                defaults.update(obj)
        except Exception:
            pass
        ADA_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        ADA_SETTINGS.write_text(json.dumps(defaults, indent=2), encoding='utf-8')
        return defaults

    def save_localtalk(self, nick, message, channel=None):
        item = {
            'time': now(),
            'network': self.state.net.get('name') if self.state.net else None,
            'channel': channel or self.state.current_channel,
            'nick': nick,
            'message': message,
        }
        try:
            rows = json.loads(LOCAL_TALK.read_text(encoding='utf-8')) if LOCAL_TALK.exists() else []
            if not isinstance(rows, list):
                rows = []
        except Exception:
            rows = []
        limit = int(self.ada_settings.get('localtalk_max_messages', 11))
        rows.append(item)
        rows = rows[-max(1, limit):]
        tmp = LOCAL_TALK.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
        tmp.replace(LOCAL_TALK)
        self.call_ada_hook('on_human_message', dict(item))

    def call_ada_hook(self, hook, context):
        for mod in list(self.extensions):
            fn = getattr(mod, hook, None)
            if callable(fn):
                try:
                    result = fn(context)
                    if hook == 'transform_outgoing' and isinstance(result, str):
                        context['message'] = result
                except Exception as exc:
                    self.log(f'[ada] plugin {getattr(mod, "__name__", "plugin")} {hook} failed: {exc}')
        return context

    def load_extensions(self):
        EXTDIR.mkdir(parents=True, exist_ok=True)
        for path in sorted(EXTDIR.glob('*.py')):
            try:
                spec = importlib.util.spec_from_file_location('greyext_' + path.stem, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self.extensions.append(mod)
            except Exception as exc:
                self.log(f'[ada] extension load failed: {path.name}: {exc}')

    def ada(self, arg=''):
        lines = [
            '[ada] Accessibility mode active.',
            '[ada] Visual PING/KICK/BAN/NickServ alerts are enabled.',
            '[ada] GUI intentionally exposes only activity status and message sending.',
            '[ada] Human chatter is retained locally as the last 11 messages.',
            f'[ada] Extension directory: {EXTDIR}',
        ]
        for mod in self.extensions:
            fn = getattr(mod, 'ada', None)
            if callable(fn):
                try:
                    extra = fn(arg)
                    if extra:
                        lines.append(str(extra))
                except Exception as exc:
                    lines.append(f'[ada] extension error: {exc}')
        for line in lines:
            self.log(line)

    def send_raw(self, line, state=None):
        state = state or self.state
        s = state.sock if state else None
        if not s or state.stop.is_set():
            return
        self.log('>> ' + redact_secrets(line))
        try:
            s.sendall((line + '\r\n').encode('utf-8', 'replace'))
        except Exception as exc:
            state.read_error = str(exc)
            state.connection_failed.set()
            raise

    def _new_state(self, net):
        nick = UNDERNET_NICK if net.get('name') == 'Undernet' else BASE_NICK
        return State(net=net, nick=nick)

    def network_has_nickserv(self, state=None):
        st = state or self.state
        name = st.net.get('name') if st and st.net else None
        return name not in {'QuakeNet', 'EFnet', 'Undernet'}

    def credentials_ready(self, need_undernet=False):
        """Return True only when the credentials required for this service exist.

        Credentials remain in /home/we6jbo/.w3Whw/account-info.json; this
        method never writes them into Wi.py, ZU.json, or the GUI log.
        """
        missing = []
        if need_undernet:
            if not UNDERNET_PASSWORD:
                missing.append('undernet_password')
        else:
            if not PASSWORD:
                missing.append('nickserv_password')
        if missing:
            self.log('[credentials] Missing required account-info.json field(s): ' + ', '.join(missing))
            self.persist({'type': 'credentials_missing',
                          'network': self.state.net.get('name') if self.state.net else None,
                          'fields': missing})
            return False
        return True

    def schedule_rizon_services(self, state):
        """After Rizon welcome, identify after 30s unless services already resolved it."""
        if state.service_timer_started:
            return
        state.service_timer_started = True

        def worker():
            deadline = time.monotonic() + RIZON_AUTO_SERVICE_DELAY
            while time.monotonic() < deadline and not state.stop.is_set():
                if self.state is not state or state.connection_failed.is_set():
                    return
                if state.authenticated.is_set():
                    return
                time.sleep(0.5)
            if self.state is not state or state.stop.is_set() or not state.sock:
                return
            if not state.authenticated.is_set():
                if not self.credentials_ready():
                    return
                self.log('[Rizon] 30 seconds after login; sending NickServ IDENTIFY.')
                self.send_raw(f'PRIVMSG NickServ :IDENTIFY {PASSWORD}', state)
                rec = self.netrec()
                rec['nickserv_target'] = 'NickServ'
                rec['identify_command'] = '/msg nickserv identify <password>'
                rec['register_command'] = '/msg nickserv register <password> <email>'
                self.persist({'type': 'rizon_auto_identify', 'network': 'Rizon',
                              'delay_seconds': RIZON_AUTO_SERVICE_DELAY})
        threading.Thread(target=worker, daemon=True, name=f'rizon-services-{state.connection_id[:8]}').start()

    def undernet_login(self, state=None):
        st = state or self.state
        if not st or not st.net or st.net.get('name') != 'Undernet' or not st.sock:
            return False
        if not self.credentials_ready(need_undernet=True):
            return
        self.send_raw(f'PRIVMSG x@channels.undernet.org :login {UNDERNET_NICK} {UNDERNET_PASSWORD}', st)
        rec = self.netrec()
        rec['cservice_target'] = 'x@channels.undernet.org'
        rec['identify_command'] = '/msg x@channels.undernet.org login we6jbo <password>'
        rec['nickserv_detected'] = False
        self.persist({'type': 'undernet_cservice_login_sent', 'network': 'Undernet',
                      'command': '/msg x@channels.undernet.org login we6jbo <password>'})
        return True

    def registration_wait_limit(self, net):
        return DALNET_REGISTRATION_WAIT_LIMIT if net.get('name') == 'DALnet' else REGISTRATION_WAIT_LIMIT

    def connect(self, net):
        last_exc = None
        for attempt in range(TLS_BAD_RECORD_RETRIES + 1):
            self.disconnect()
            time.sleep(0.15)
            state = self._new_state(net)
            self.state = state
            if attempt:
                self.log(f"[connect] retry {attempt}/{TLS_BAD_RECORD_RETRIES} for {net['name']} after TLS bad record")
                self.persist({'type': 'tls_retry', 'network': net['name'], 'attempt': attempt})
            self.log(f"[connect] {net['name']} {net['host']}:{net['port']}")
            try:
                raw = socket.create_connection((net['host'], net['port']), timeout=25)
                raw.settimeout(1.0)
                if net['tls']:
                    ctx = ssl.create_default_context()
                    sock = ctx.wrap_socket(raw, server_hostname=net['host'])
                    sock.settimeout(1.0)
                else:
                    sock = raw
                state.sock = sock
                rec = self.netrec()
                rec['server'] = {'host': net['host'], 'port': net['port'], 'tls': net['tls']}
                rec['message_command'] = '/msg #target message'
                self.persist()
                self.send_raw(f'NICK {state.nick}', state)
                self.send_raw(f'USER we6jbo 0 * :{CLIENT_NAME}', state)
                t = threading.Thread(target=self.reader, args=(state,), daemon=True, name=f'irc-reader-{state.connection_id[:8]}')
                state.reader_thread = t
                t.start()

                wait_limit = self.registration_wait_limit(net)
                if net['name'] == 'DALnet':
                    self.log('[Waiting for DALnet login]')
                    self.persist({'type': 'dalnet_login_wait_started', 'network': 'DALnet',
                                  'wait_limit_seconds': wait_limit, 'connection_id': state.connection_id})
                self.log(f'[connect] waiting up to {wait_limit}s for IRC welcome (001)')
                deadline = time.monotonic() + wait_limit
                while time.monotonic() < deadline:
                    if state.registered.wait(0.25):
                        break
                    if state.tls_bad_record.is_set() or state.connection_failed.is_set():
                        break
                if not state.registered.is_set():
                    if state.tls_bad_record.is_set() and attempt < TLS_BAD_RECORD_RETRIES:
                        last_exc = ConnectionError(state.read_error or 'TLS bad record')
                        self.disconnect(state)
                        time.sleep(2.0)
                        continue
                    if state.connection_failed.is_set():
                        raise ConnectionError(state.read_error or 'connection failed during IRC registration')
                    self.persist({'type': 'irc_registration_timeout', 'network': net['name'], 'connection_id': state.connection_id, 'waited_seconds': wait_limit})
                    raise TimeoutError(f'IRC registration timed out after {wait_limit} seconds')

                rec = self.netrec()
                if self.network_has_nickserv(state):
                    ns_target = self.nickserv_target(state)
                    self.send_raw(f'PRIVMSG {ns_target} :HELP REGISTER', state)
                    self.send_raw(f'PRIVMSG {ns_target} :HELP IDENTIFY', state)
                    rec['nickserv_target'] = ns_target
                    if net['name'] == 'DALnet':
                        rec['register_command'] = '/msg NickServ@services.dal.net REGISTER <password> <email>'
                        rec['identify_command'] = '/msg NickServ@services.dal.net IDENTIFY <password>'
                    elif net['name'] == 'Rizon':
                        rec['register_command'] = '/msg nickserv register <password> <email>'
                        rec['identify_command'] = '/msg nickserv identify <password>'
                    self.persist()
                else:
                    rec['nickserv_detected'] = False
                    rec['nickserv_target'] = None
                    self.persist()
                    self.log(f"[services] {net['name']}: NickServ is not used by this client.")
                if net['name'] == 'Libera.Chat':
                    self.log('[NICKSERV] Libera.Chat connected; automatically identifying the registered nickname.')
                    self.identify_nick()
                elif net['name'] == 'Rizon':
                    self.schedule_rizon_services(state)
                elif net['name'] == 'Undernet':
                    self.log('[Undernet] Using nickname we6jbo and identifying with X/CService.')
                    self.undernet_login(state)
                return True
            except Exception as exc:
                last_exc = exc
                bad = 'DECRYPTION_FAILED_OR_BAD_RECORD_MAC' in str(exc).upper() or state.tls_bad_record.is_set()
                self.disconnect(state)
                if bad and attempt < TLS_BAD_RECORD_RETRIES:
                    self.log(f"[tls] {net['name']}: bad TLS record; retrying this server once")
                    self.persist({'type': 'tls_bad_record', 'network': net['name'], 'action': 'retry_once', 'error': str(exc)})
                    time.sleep(2.0)
                    continue
                raise
        if last_exc:
            raise last_exc
        return False

    def disconnect(self, state=None):
        old = state or getattr(self, 'state', None)
        if not old:
            return
        if old is self.state and old.talking:
            self.set_talking(False, old.current_channel)
        old.stop.set()
        sock = old.sock
        old.sock = None
        if sock:
            try:
                sock.sendall(b'QUIT :greyircclient rotating\r\n')
            except Exception:
                pass
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass
        t = old.reader_thread
        if t and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=CONNECTION_HANDOFF_GRACE)
        old.reader_thread = None

    def reader(self, state):
        buf = b''
        sock = state.sock
        cid = state.connection_id
        while not state.stop.is_set() and sock:
            # Once another connection owns self.state, this reader is obsolete.
            if self.state is not state or self.state.connection_id != cid:
                self.log(f'[read] stale connection {cid[:8]} retired')
                break
            try:
                chunk = sock.recv(8192)
                if not chunk:
                    state.connection_failed.set()
                    state.read_error = 'server closed connection'
                    break
                buf += chunk
                while b'\n' in buf:
                    raw, buf = buf.split(b'\n', 1)
                    if self.state is not state or self.state.connection_id != cid:
                        return
                    self.handle(raw.rstrip(b'\r').decode('utf-8', 'replace'), state)
            except socket.timeout:
                continue
            except Exception as exc:
                if state.stop.is_set():
                    break
                msg = str(exc)
                state.read_error = msg
                state.connection_failed.set()
                if 'DECRYPTION_FAILED_OR_BAD_RECORD_MAC' in msg.upper():
                    state.tls_bad_record.set()
                    self.log(f'[read] TLS bad record on {state.net["name"]} connection {cid[:8]}; retiring only this socket')
                    self.persist({'type': 'tls_bad_record', 'network': state.net['name'], 'connection_id': cid, 'error': msg})
                else:
                    self.log(f'[read] {state.net["name"]} connection {cid[:8]}: {msg}')
                break

    @staticmethod
    def parse(line):
        prefix = ''
        if line.startswith(':'):
            prefix, line = line[1:].split(' ', 1)
        if ' :' in line:
            before, trailing = line.split(' :', 1)
            parts = before.split() + [trailing]
        else:
            parts = line.split()
        return prefix, parts[0] if parts else '', parts[1:]

    def handle(self, line, state=None):
        state = state or self.state
        if state is not self.state or state.connection_id != self.state.connection_id:
            return
        shown = redact_secrets(line)
        self.log('<< ' + shown)
        prefix, cmd, args = self.parse(line)
        low = line.lower()

        protected = re.search(r'this channel is protected, you may need to wait\s+(\d+)\s+seconds?\s+before being able to talk', line, re.I)
        if protected:
            channel = next((a for a in args if isinstance(a, str) and a.startswith('#')), self.state.current_channel)
            if channel and channel == self.state.current_channel:
                self.apply_channel_protection(int(protected.group(1)), channel, shown)

        if cmd == 'PING':
            token = args[-1] if args else ''
            self.send_raw('PONG :' + token)
            return

        if cmd == '001':
            self.state.registered.set()
            if self.state.net and self.state.net.get('name') == 'DALnet':
                self.log('[Stop talking]')
                self.log('[DALnet login ready] NickServ commands are now enabled.')
                self.persist({'type': 'dalnet_login_ready', 'network': 'DALnet',
                              'connection_id': self.state.connection_id})
        elif cmd == '900':
            self.state.authenticated.set()
            self.persist({'type': 'nickserv_authenticated', 'network': self.state.net['name'] if self.state.net else None, 'nick': self.state.nick})
        elif cmd == '433':
            suffix = str(int(time.time()) % 90 + 10)
            self.state.nick = (BASE_NICK[:7] + suffix)[:9]
            self.send_raw('NICK ' + self.state.nick)
        elif cmd == '322' and len(args) >= 3:
            try:
                self.state.list_rows.append((int(args[2]), args[1], args[3] if len(args) > 3 else ''))
            except ValueError:
                pass
        elif cmd == '323':
            self.state.list_done.set()
        elif cmd == '474':
            self.state.banned.set()
            self.record_ban(line, server=False)
        elif cmd == 'KICK' and len(args) >= 2:
            channel, target = args[0], args[1]
            if target.lower() == self.state.nick.lower():
                self.state.kicked.set()
                self.set_talking(False, channel)
                self.netrec()['kick_events'].append({'time': now(), 'channel': channel, 'raw': shown})
                self.persist()
        elif cmd == 'JOIN' and args:
            nick = prefix.split('!', 1)[0]
            channel = args[0]
            if nick.lower() == self.state.nick.lower() and channel == self.state.current_channel:
                self.state.joined.set()
                self.state.last_human_activity = time.monotonic()
                self.state.human_messages_seen = 0
                self.set_talking(False, channel)
                self.log(f'[channel] joined {channel}; waiting for human activity')
        elif cmd == 'PART' and args:
            nick = prefix.split('!', 1)[0]
            channel = args[0]
            if nick.lower() == self.state.nick.lower():
                self.set_talking(False, channel)
                if self.state.current_channel == channel:
                    self.state.current_channel = None
        elif cmd in {'471', '473', '474', '475', '476', '477', '489'}:
            # Common channel-join failures. 474 is also recorded above as a ban.
            self.state.join_failed.set()
        elif cmd == 'PRIVMSG' and len(args) >= 2:
            nick = prefix.split('!', 1)[0]
            target, msg = args[0], args[1]
            if msg == '\x01VERSION\x01':
                self.send_raw(f'NOTICE {nick} :\x01VERSION {CLIENT_NAME}\x01')
            if target.startswith('#') and target == self.state.current_channel:
                if not self.is_bot(nick, msg):
                    tick = time.monotonic()
                    self.state.chatter.append((tick, nick, msg))
                    self.state.last_human_activity = tick
                    self.state.human_messages_seen += 1
                    self.save_localtalk(nick, msg, target)
                    if self.protection_remaining() <= 0:
                        self.set_talking(True, target)
        elif cmd == 'ERROR' and BAN_RE.search(line):
            self.state.server_banned.set()
            self.record_ban(line, server=True)

        # Treat only actual ban responses directed at us as bans. LIST topics, NAMES
        # lists and capability advertisements can contain the words ban/kick without
        # meaning that this client has been banned.
        if cmd == '465':
            self.state.server_banned.set()
            self.record_ban(line, server=True)
        elif cmd in {'NOTICE', 'PRIVMSG'} and args:
            service_text = args[-1].lower().replace('\x02', '')
            directed_to_us = args[0].lower() == self.state.nick.lower() if args else False
            if directed_to_us and re.search(r'\b(?:you (?:are|have been) banned|k-?lined|g-?lined|z-?lined|akilled)\b', service_text, re.I):
                self.state.server_banned.set()
                self.record_ban(line, server=True)

        if NS_RE.search(prefix) or ('nickserv' in low and cmd in {'NOTICE', 'PRIVMSG'}):
            self.learn_nickserv(prefix, args, shown)


    def nickserv_target(self, state=None):
        """Return the service target required by the active IRC network."""
        st = state or self.state
        name = st.net.get('name') if st and st.net else None
        if name == 'DALnet':
            return 'NickServ@services.dal.net'
        return 'NickServ'

    def nickserv_ready(self, action='NickServ command'):
        """Gate services commands until the active network can accept them."""
        st = self.state
        if st and st.net and not self.network_has_nickserv(st):
            self.log(f"[NICKSERV] {st.net.get('name')} does not use NickServ in this client.")
            return False
        if st and st.net and st.net.get('name') == 'DALnet' and not st.registered.is_set():
            self.log('[Waiting for DALnet login]')
            self.log(f'[NICKSERV] {action} held: DALnet has not sent IRC welcome numeric 001 yet.')
            self.persist({'type': 'dalnet_nickserv_held', 'network': 'DALnet',
                          'action': action, 'reason': 'waiting_for_001'})
            return False
        return True

    def record_nickserv_method(self, kind, target=None):
        """Persist the network-specific NickServ command format without exposing the password."""
        rec = self.netrec()
        target = target or self.nickserv_target()
        rec['nickserv_target'] = target
        network = self.state.net.get('name') if self.state and self.state.net else None
        if network == 'Rizon':
            if kind == 'identify':
                rec['identify_command'] = '/msg nickserv identify <password>'
                rec['identify_command_used'] = '/msg nickserv identify <password>'
            elif kind == 'register':
                rec['register_command'] = '/msg nickserv register <password> <email>'
                rec['register_command_used'] = '/msg nickserv register <password> <email>'
        elif kind == 'identify':
            rec['identify_command'] = f'/msg {target} IDENTIFY <password>'
            rec['identify_command_used'] = f'/msg {target} IDENTIFY <password>'
        elif kind == 'register':
            rec['register_command'] = f'/msg {target} REGISTER <password> <email>'
            rec['register_command_used'] = f'/msg {target} REGISTER <password> <email>'
        self.persist()

    def learn_nickserv(self, prefix, args, shown):
        rec = self.netrec()
        rec['nickserv_detected'] = True
        msg = args[-1] if args else shown
        self.log('[NICKSERV] ' + msg)
        ml = msg.lower().replace('\x02', '')
        if self.state.net and self.state.net.get('name') == 'Rizon':
            rec['nickserv_target'] = 'NickServ'
            rec['register_command'] = '/msg nickserv register <password> <email>'
            rec['identify_command'] = '/msg nickserv identify <password>'
            # If Rizon explicitly asks us to identify, do it immediately instead of waiting for the 30s timer.
            if ('identify' in ml and any(x in ml for x in ('please', 'must', 'need', 'required', 'registered nickname'))
                    and not self.state.authenticated.is_set()):
                if not self.credentials_ready():
                    return
                self.log('[Rizon] NickServ requested identification; identifying now.')
                self.send_raw(f'PRIVMSG NickServ :IDENTIFY {PASSWORD}')
                self.persist({'type': 'rizon_identify_when_told', 'network': 'Rizon'})
        if self.state.net and self.state.net.get('name') == 'DALnet':
            rec['nickserv_target'] = 'NickServ@services.dal.net'
            if 'usage: register <password> <email>' in ml:
                rec['register_command'] = '/msg NickServ@services.dal.net REGISTER <password> <email>'
            if 'usage: identify <password>' in ml:
                rec['identify_command'] = '/msg NickServ@services.dal.net IDENTIFY <password>'
            self.persist()
        if ('already logged in as' in ml or 'now logged in as' in ml or
                'has now been verified' in ml or 'you are now identified' in ml):
            self.state.authenticated.set()
            self.state.identity_attention.clear()
            rec['authenticated'] = True
            rec['authenticated_time'] = now()
        if self.state.net and self.state.net.get('name') == 'DALnet' and any(
                phrase in ml for phrase in ('captcha', 'verification code', 'verify your', 'complete verification')):
            if not self.state.authenticated.is_set():
                self.state.identity_attention.set()
                self.log('***H-Key*** DALnet NickServ requires manual verification; traversal timers are paused.')
                self.persist({'type': 'dalnet_manual_verification', 'network': 'DALnet', 'message': msg})

        attention_phrases = (
            'please identify', 'you need to identify', 'must identify',
            'nickname is registered', 'nick is registered',
            'nickname is not registered', 'nick is not registered',
            'register your nickname', 'register this nickname',
            'identify to your nickname', 'identify for your nickname'
        )
        if any(phrase in ml for phrase in attention_phrases) and not (ml.startswith('syntax:') or 'help' in ml[:40]):
            if not self.state.authenticated.is_set():
                self.state.identity_attention.set()
                self.log('***H-Key*** NickServ registration/identification needs attention; traversal timer is paused.')
                self.persist({'type': 'nickserv_attention', 'network': self.state.net['name'] if self.state.net else None,
                              'message': msg})
                if any(p in ml for p in ('nickname is not registered', 'nick is not registered', "isn't registered", 'not a registered nickname')):
                    self.log('[NICKSERV] nickname appears unregistered; attempting automatic registration.')
                    self.register_nick()
                elif 'identify' in ml:
                    self.identify_nick()
        if 'register' in msg.lower():
            rec['nickserv_register_help'].append(msg)
            rec['nickserv_register_help'] = rec['nickserv_register_help'][-30:]
            found = REGISTER_RE.search(msg)
            if found:
                rec['register_command'] = found.group(0)
        if 'identify' in msg.lower() or 'identify' in shown.lower():
            rec['nickserv_identify_help'].append(msg)
            rec['nickserv_identify_help'] = rec['nickserv_identify_help'][-30:]
            found = IDENTIFY_RE.search(msg)
            if found:
                rec['identify_command'] = found.group(0)
        self.persist()

    def identify_nick(self):
        if self.state.net and self.state.net.get('name') == 'Undernet':
            return self.undernet_login()
        if not self.nickserv_ready('IDENTIFY'):
            return False
        target = self.nickserv_target()
        if not self.credentials_ready():
            return
        self.send_raw(f'PRIVMSG {target} :IDENTIFY {PASSWORD}')
        self.record_nickserv_method('identify', target)
        return True

    def register_nick(self):
        if not self.nickserv_ready('REGISTER'):
            return False
        target = self.nickserv_target()
        if not self.credentials_ready(need_email=True):
            return
        self.send_raw(f'PRIVMSG {target} :REGISTER {PASSWORD} {EMAIL}')
        self.record_nickserv_method('register', target)
        return True

    def record_ban(self, line, server=False):
        rec = self.netrec()
        item = {'time': now(), 'scope': 'server' if server else 'channel', 'raw': redact_secrets(line)}
        rec['ban_events'].append(item)
        self.persist()
        self.log('[BAN ALERT] waiting 30 seconds before rotating')

    def is_bot(self, nick, msg):
        n = nick.lower().strip('[]{}_-`^')
        if n in {'nickserv', 'chanserv', 'memoserv', 'operserv', 'hostserv', 'q', 'x'}:
            return True
        if BOT_RE.search(nick):
            return True
        if msg.startswith('\x01') and msg.endswith('\x01'):
            return True
        return False

    def unofficial(self, channel, topic):
        text = (channel.lstrip('#') + ' ' + topic).lower()
        words = set(re.findall(r'[a-z0-9]+', text))
        if words & OFFICIAL_WORDS:
            return False
        if channel.lower() in {'#help', '#support', '#staff', '#channel'}:
            return False
        return True

    def get_candidates(self):
        self.state.list_rows.clear()
        self.state.list_done.clear()
        self.send_raw('LIST')
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline and not self.state.list_done.is_set():
            if self.state.connection_failed.is_set():
                raise ConnectionError(self.state.read_error or 'connection failed while listing channels')
            time.sleep(0.25)
        if not self.state.list_done.is_set():
            self.log('[list] timed out; using rows received so far')

        netname = self.state.net.get('name') if self.state.net else ''
        base = [r for r in self.state.list_rows if r[0] >= 5 and r[1].lower() != '#channel']
        by_name = {r[1].lower(): r for r in base}

        # Explicit network choices requested by the user are kept first. LIST is still
        # used, and absent requested channels are represented as zero-count fallbacks
        # so a manual JOIN can determine whether they exist.
        requested = {
            'Rizon': ['#chatfriendly'],
            'QuakeNet': ['#chat', '#advice', '#gamer'],
            'EFnet': ['#videogames'],
            'Undernet': ['#ireland', '#elite', '#gov', '#EGG'],
        }.get(netname, [])
        if requested:
            preferred = []
            for channel in requested:
                row = by_name.get(channel.lower())
                preferred.append(row if row else (0, channel, 'requested channel'))
            # Rizon should use only #chatfriendly. The other named networks can fall
            # back to remaining LIST results after their requested channels.
            if netname == 'Rizon':
                return preferred
            remaining = [r for r in base if r[1].lower() not in {c.lower() for c in requested}
                         and self.unofficial(r[1], r[2])]
            remaining.sort(reverse=True, key=lambda x: x[0])
            return preferred + remaining

        rows = [r for r in base if self.unofficial(r[1], r[2])]
        if netname == 'DALnet':
            def dal_priority(row):
                count, channel, topic = row
                c = channel.lower()
                text = (channel + ' ' + topic).lower()
                if c == '#rpg':
                    return (5, count)
                if c == '#rpgnet':
                    return (4, count)
                if 'darksouls' in text or 'dark-souls' in text or 'dark_souls' in text or ('dark' in text and 'souls' in text):
                    return (3, count)
                if 'rpg' in text:
                    return (2, count)
                return (1, count)
            rows.sort(reverse=True, key=dal_priority)
        else:
            rows.sort(reverse=True, key=lambda x: x[0])
        return rows

    def temp_window_active(self):
        local_now = datetime.now()
        return TEMP_START <= local_now < TEMP_END

    def temp_mode_active(self):
        if self.temp_30_enabled and not self.temp_window_active():
            self.temp_30_enabled = False
            self.log('[temporary] Aug 15 17:41-18:41 mode has expired; normal rules are active.')
            self.persist({'type': 'temporary_one_channel_mode_expired', 'remark': TEMP_REMARK})
        return self.temp_30_enabled and self.temp_window_active()

    def enable_temp_30(self):
        if not self.temp_window_active():
            self.temp_30_enabled = False
            self.log('[temporary] The Aug 15 17:41-18:41 window is not active; normal rules remain in effect.')
            return
        if self.temp_traversal_running:
            self.log('[temporary] The one-channel-per-server traversal is already running.')
            return
        self.temp_30_enabled = True
        self.log('[temporary] One-channel-per-server traversal enabled until Aug 15, 2026 18:41.')
        self.log('[temporary] ' + TEMP_REMARK)
        self.persist({'type': 'temporary_one_channel_mode_enabled', 'remark': TEMP_REMARK})
        self.temp_traversal_running = True
        threading.Thread(target=self._temporary_traversal, daemon=True).start()

    def identity_ready_or_wait(self):
        # Normal IRC registration (001) must complete before channel work.
        if not self.state.registered.is_set():
            if not self.state.registered.wait(self.registration_wait_limit(self.state.net or {})):
                return False

        rec = self.netrec()
        nickserv_seen = bool(rec.get('nickserv_detected'))
        needs_attention = self.state.identity_attention.is_set()
        if self.state.authenticated.is_set():
            return True
        # NickServ HELP by itself is informational and must not stall traversal.
        # Libera is special because connect() has already sent IDENTIFY, so wait
        # for confirmation there. Other networks pause only after an actual
        # registration/identification-needed indication.
        libera_pending = bool(self.state.net and self.state.net['name'] == 'Libera.Chat' and nickserv_seen)
        if not needs_attention and not libera_pending:
            return True

        # A NickServ issue pauses channel timing. Give the user up to five minutes
        # to register/identify; successful authentication resumes immediately.
        self.log('***H-Key*** Waiting for NickServ registration/identification before channel timing.')
        self.persist({'type': 'identity_wait_started', 'network': self.state.net['name'] if self.state.net else None,
                      'wait_limit_seconds': IDENTITY_WAIT_LIMIT})
        deadline = time.monotonic() + IDENTITY_WAIT_LIMIT
        while time.monotonic() < deadline and self.state.sock and not self.state.stop.is_set():
            if self.state.authenticated.wait(1.0):
                self.log('[NICKSERV] Registration/identification confirmed; paused traversal may resume.')
                return True
        self.log('[NICKSERV] Five-minute identity wait ended without confirmation; this server will be recorded and traversal may continue.')
        self.persist({'type': 'identity_wait_timeout', 'network': self.state.net['name'] if self.state.net else None,
                      'waited_seconds': IDENTITY_WAIT_LIMIT})
        return False

    def _temporary_traversal(self):
        try:
            for idx, net in enumerate(NETWORKS):
                if not self.temp_mode_active() or self.state.stop.is_set():
                    break
                try:
                    self.connect(net)
                    time.sleep(1)
                    rec = self.netrec()
                    if rec.get('nickserv_detected') and not self.state.authenticated.is_set():
                        self.log('***H-Key*** NickServ detected. Identify or register if the service requires it.')
                    # Libera auto-identify remains enabled by connect(). Other networks can
                    # be handled through the NickServ box or by targeting NickServ below.
                    rows = self.get_candidates()
                    if not rows:
                        self.log(f"[temporary] {net['name']}: no qualifying candidate channel was available.")
                        self.persist({'type': 'temporary_server_result', 'network': net['name'], 'qualified': False,
                                      'reason': 'no_candidate_channel', 'remark': TEMP_REMARK})
                        continue
                    count, channel, topic = rows[0]
                    ok = self.test_channel(count, channel, topic, 30)
                    self.persist({'type': 'temporary_server_result', 'network': net['name'], 'channel': channel,
                                  'qualified': bool(ok), 'remark': TEMP_REMARK})
                except Exception as exc:
                    self.log(f"[temporary] {net['name']}: {exc}")
                    self.persist({'type': 'temporary_server_error', 'network': net['name'], 'error': str(exc),
                                  'remark': TEMP_REMARK})
                finally:
                    self.disconnect()
            else:
                if self.temp_mode_active():
                    self.log('*** * PENGUIN * ***')
                    self.persist({'type': 'temporary_all_servers_visited', 'message': '* PENGUIN *',
                                  'remark': TEMP_REMARK})
        finally:
            self.temp_traversal_running = False

    def test_channel(self, count, channel, topic, dwell=120):
        """Join a channel and remain while real human activity continues.

        There is an initial two-minute window for a human-looking PRIVMSG. After
        activity starts, every human message resets the two-minute inactivity
        deadline. Bot-only traffic never starts or resets the deadline.
        """
        state = self.state
        state.current_channel = channel
        state.chatter.clear()
        state.kicked.clear()
        state.banned.clear()
        state.joined.clear()
        state.join_failed.clear()
        state.protected_until = 0.0
        state.protected_seconds = 0
        state.human_messages_seen = 0
        state.last_human_activity = time.monotonic()
        self.set_talking(False, channel)
        self.log(f'[channel] attempting {channel} ({count} listed users)')
        if not self.wait_action_gap('JOIN', channel):
            state.current_channel = None
            return False
        self.send_raw('JOIN ' + channel)
        join_deadline = time.monotonic() + 30
        while time.monotonic() < join_deadline and not state.joined.is_set():
            if state.connection_failed.is_set():
                raise ConnectionError(state.read_error or 'connection failed while joining channel')
            if state.join_failed.is_set() or state.kicked.is_set() or state.banned.is_set() or state.server_banned.is_set():
                break
            time.sleep(0.2)
        if not state.joined.is_set():
            self.set_talking(False, channel)
            state.current_channel = None
            return False

        if not self.identity_ready_or_wait():
            if state.sock and self.wait_action_gap('PART', channel):
                self.send_raw('PART ' + channel + ' :identity pending')
            self.set_talking(False, channel)
            state.current_channel = None
            return False

        timeout = float(self.ada_settings.get('human_activity_timeout_seconds', 120))
        active_seen = False
        while not state.stop.is_set() and not self.global_stop.is_set():
            if self.user_suspended:
                break
            if state.connection_failed.is_set():
                raise ConnectionError(state.read_error or 'connection failed during channel activity wait')
            if state.server_banned.is_set() or state.banned.is_set() or state.kicked.is_set() or state.join_failed.is_set():
                break
            # Channel protection pauses inactivity accounting by extending the last
            # activity marker for the duration of the server-mandated wait.
            protection = self.protection_remaining()
            if protection > 0:
                self.set_talking(False, channel)
                state.last_human_activity = time.monotonic()
                time.sleep(min(0.5, protection))
                continue
            if state.human_messages_seen > 0:
                active_seen = True
            idle = time.monotonic() - state.last_human_activity
            if idle >= timeout:
                self.set_talking(False, channel)
                self.log(f'[channel] {channel}: no human activity for {int(timeout)} seconds; rotating')
                self.persist({'type': 'channel_inactive', 'network': state.net.get('name') if state.net else None,
                              'channel': channel, 'human_messages': state.human_messages_seen,
                              'observed_seconds': int(timeout)})
                break
            time.sleep(0.25)

        rec = self.netrec()
        rec.setdefault('channel_tests', []).append({
            'time': now(), 'channel': channel, 'listed_users': count, 'joined': True,
            'observed_seconds': int(timeout), 'human_looking_messages': state.human_messages_seen,
            'qualified': active_seen,
            'remark': 'Human activity starts [Start talking]; two minutes without human activity rotates to the next channel.'
        })
        rec['channel_tests'] = rec['channel_tests'][-200:]
        if active_seen and channel not in rec['successful_channels']:
            rec['successful_channels'].append(channel)
        self.persist()
        if state.sock and state.joined.is_set() and self.wait_action_gap('PART', channel):
            try:
                self.send_raw('PART ' + channel + ' :inactive')
            except Exception:
                pass
        self.set_talking(False, channel)
        state.current_channel = None
        return active_seen

    def send_nickserv(self, text):
        text = text.strip()
        if not text:
            self.log('[NICKSERV] Enter a NickServ command first.')
            return
        action = text.split(maxsplit=1)[0].upper() if text else 'NickServ command'
        if not self.nickserv_ready(action):
            return
        target = self.nickserv_target()
        self.send_raw(f'PRIVMSG {target} :' + text)
        low = text.lower()
        if low.startswith('identify '):
            self.record_nickserv_method('identify', target)
        elif low.startswith('register '):
            self.record_nickserv_method('register', target)
        self.persist({'type': 'nickserv_manual', 'network': self.state.net['name'] if self.state.net else None,
                      'target': target, 'command': redact_secrets(text)})

    def _manual_worker(self):
        try:
            remaining = self.manual_cooldown_until - time.monotonic()
            if remaining > 0:
                self.log(f'[manual] Wait {int(remaining + 0.999)} more seconds after the ban/kick before advancing.')
                return

            need_network = (
                self.state.net is None or
                self.state.sock is None or
                self.manual_successes >= 5 or
                self.state.server_banned.is_set() or
                self.manual_row_index >= len(self.manual_rows)
            )

            if need_network:
                self.disconnect()
                self.manual_net_index += 1
                if self.manual_net_index >= len(NETWORKS):
                    self.log('[manual] All configured networks have been visited. Press > to start over.')
                    self.manual_net_index = -1
                    self.manual_rows = []
                    self.manual_row_index = 0
                    self.manual_successes = 0
                    self.state = State()
                    return

                net = NETWORKS[self.manual_net_index]
                self.connect(net)
                time.sleep(1)
                if self.netrec().get('nickserv_detected'):
                    self.log('[NICKSERV] NickServ detected. Use the NickServ entry or Identify/Register buttons as needed.')
                self.manual_rows = self.get_candidates()
                self.manual_row_index = 0
                self.manual_successes = 0
                self.log(f"[manual] {net['name']} ready with {len(self.manual_rows)} candidate channels. Press > for the next channel.")
                return

            count, channel, topic = self.manual_rows[self.manual_row_index]
            self.manual_row_index += 1
            was_kicked = False
            was_banned = False
            was_server_banned = False
            ok = self.test_channel(count, channel, topic, 120)
            was_kicked = self.state.kicked.is_set()
            was_banned = self.state.banned.is_set()
            was_server_banned = self.state.server_banned.is_set()
            if ok:
                self.manual_successes += 1
                self.log(f'[manual] {self.manual_successes}/5 successful channels on this network. Press > to continue.')
            else:
                self.log('[manual] Channel did not qualify. Press > to continue.')
            if was_kicked or was_banned or was_server_banned:
                self.manual_cooldown_until = time.monotonic() + 30
                self.log('[manual] 30-second ban/kick cooldown started.')
        except Exception as exc:
            netname = self.state.net['name'] if self.state.net else 'none'
            self.log(f'[manual] {netname}: {exc}')
            self.persist({'type': 'manual_error', 'network': netname, 'error': str(exc)})
            self.disconnect()
            self.state = State()
        finally:
            self.manual_busy.release()

    def manual_next(self):
        if not self.manual_busy.acquire(blocking=False):
            self.log('[manual] Current step is still running.')
            return
        threading.Thread(target=self._manual_worker, daemon=True).start()

    def automate_services(self):
        st = self.state
        if not st.net or not st.registered.is_set():
            return
        name = st.net.get('name')
        # connect() already handles Undernet X/CService, Libera.Chat automatic
        # identification, and Rizon's required 30-second delayed identification.
        if name in {'Undernet', 'Libera.Chat', 'Rizon'}:
            return
        if not self.network_has_nickserv(st):
            return
        self.identify_nick()

    def rotate(self):
        while not self.global_stop.is_set():
            for net in NETWORKS:
                if self.global_stop.is_set():
                    break
                if not self._wait_for_user_resume():
                    break
                try:
                    self.connect(net)
                    self.automate_services()
                    time.sleep(2)
                    rows = self.get_candidates()
                    active_channels = 0
                    for count, channel, topic in rows:
                        if self.global_stop.is_set() or self.user_suspended or self.state.server_banned.is_set():
                            break
                        was_active = self.test_channel(count, channel, topic, 120)
                        if was_active:
                            active_channels += 1
                        if self.state.server_banned.is_set():
                            break
                        if active_channels >= 5:
                            break
                    if self.state.server_banned.is_set():
                        self.log(f'[server] {net["name"]}: ban detected; moving to next server')
                except Exception as exc:
                    self.log(f"[network] {net['name']}: {exc}")
                    self.persist({'type': 'network_error', 'network': net['name'], 'error': str(exc)})
                finally:
                    self.disconnect()
            if not self.global_stop.is_set() and not self.user_suspended:
                self.log('[rotate] all configured networks visited; beginning another cycle')
                time.sleep(2)

    def start_rotation(self):
        self.global_stop.clear()
        self.user_resume_event.set()
        self.state.stop.clear()
        if self.rotation_thread and self.rotation_thread.is_alive():
            return
        self.rotation_thread = threading.Thread(target=self.rotate, daemon=True, name='irc-auto-rotation')
        self.rotation_thread.start()

    def stop_rotation(self):
        self.global_stop.set()
        self.state.stop.set()
        self.disconnect()

    def send_message(self, target, message, count_as_user_input=True):
        message = str(message)
        if not message:
            return False
        if count_as_user_input:
            self.note_user_input()

        target = (target or self.state.current_channel or '').strip()
        if self.user_suspended or not target or not self.state.sock or target != self.state.current_channel:
            with self.presence_lock:
                self.pending_outgoing = message
            # note_user_input() wakes a suspended rotate thread and changes the
            # idle input-ready Start talking display back to Stop talking. Keep it
            # there until genuine human channel activity is detected, then send.
            if self.user_suspended:
                self.note_user_input()
            self.log('[send] Message queued; it will be sent after IRC reconnects and human activity starts in the current channel.')
            self.persist({'type': 'outgoing_message_queued', 'characters': len(message)})
            return True

        if not target.startswith('#'):
            return False
        if self.protection_remaining() > 0:
            self.set_talking(False, target)
            return False
        context = self.call_ada_hook('transform_outgoing', {
            'network': self.state.net.get('name') if self.state.net else None,
            'channel': target,
            'message': message,
        })
        message = str(context.get('message', message))
        low, high = self.ada_settings.get('send_delay_seconds_per_character', [2.3, 2.7])
        delay = sum(random.uniform(float(low), float(high)) for _ in message)
        self.log(f'[send] waiting {delay:.1f}s before sending {len(message)} characters to {target}')
        state = self.state
        cid = state.connection_id
        def worker():
            deadline = time.monotonic() + delay
            while time.monotonic() < deadline:
                if self.state is not state or state.connection_id != cid or state.stop.is_set() or state.connection_failed.is_set():
                    # Preserve an unsent user message across automatic rotation.
                    with self.presence_lock:
                        if self.pending_outgoing is None:
                            self.pending_outgoing = message
                    return
                if self.protection_remaining() > 0:
                    deadline += self.protection_remaining()
                time.sleep(0.2)
            if self.state is state and state.current_channel == target and state.sock and not state.stop.is_set():
                self.send_raw(f'PRIVMSG {target} :{message}', state)
                self.persist({'type': 'outgoing_channel_message', 'network': state.net.get('name') if state.net else None,
                              'channel': target, 'characters': len(message), 'delay_seconds': round(delay, 3)})
        threading.Thread(target=worker, daemon=True, name='delayed-channel-send').start()
        return True



class DiagnosticStore:
    """Atomic, bounded health/event log for the headless Local Talk service."""
    def __init__(self):
        self.lock = threading.Lock()
        self.started = now()
        self.events = []
        self.current = {
            'running': True,
            'control_host': CONTROL_HOST,
            'control_port': CONTROL_PORT,
            'bbs_connected': False,
            'irc_connected': False,
            'network': None,
            'channel': None,
            'status': '[Stop talking]',
            'user_suspended': False,
            'last_irc_activity': None,
            'last_human_message': None,
            'last_outgoing_message': None,
            'last_error': None,
        }
        self.write()

    def classify(self, event):
        et = str(event.get('type', 'event'))
        if any(x in et for x in ('error', 'timeout', 'failed', 'ban')):
            return 'error' if 'error' in et or 'failed' in et else 'warning'
        return 'info'

    def add(self, event, severity=None):
        with self.lock:
            row = dict(event)
            row.setdefault('time', now())
            row.setdefault('severity', severity or self.classify(row))
            self.events.append(row)
            self.events = self.events[-200:]
            if row['severity'] in {'warning', 'error'}:
                self.current['last_error'] = {
                    'time': row['time'], 'type': row.get('type'),
                    'message': row.get('error') or row.get('message') or row.get('reason')
                }
            self._write_locked()

    def update(self, **changes):
        with self.lock:
            self.current.update(changes)
            self._write_locked()

    def write(self):
        with self.lock:
            self._write_locked()

    def _write_locked(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        payload = {
            'client': 'localchat',
            'started': self.started,
            'last_updated': now(),
            'current_state': dict(self.current),
            'events': list(self.events),
        }
        tmp = ERRORS.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        tmp.replace(ERRORS)
        state_payload = {
            'client': 'localchat',
            'last_updated': payload['last_updated'],
            **dict(self.current),
        }
        stmp = STATE_FILE.with_suffix('.json.tmp')
        stmp.write_text(json.dumps(state_payload, indent=2, ensure_ascii=False), encoding='utf-8')
        stmp.replace(STATE_FILE)


class LocalChatDaemon:
    def __init__(self):
        self.diag = DiagnosticStore()
        self.client = Client(self.emit, self.diag.add)
        self.guard = InstanceGuard(self.emit)
        self.shutdown_event = threading.Event()
        self.server = None
        self.last_status = '[Stop talking]'
        self.last_join_seen = 0.0
        self.last_network_seen = 0.0
        self.last_identify_attention = 0.0
        self.last_human_seen = 0.0
        self.guard.watch(self.replaced_by_new_instance)

    def emit(self, line):
        text = str(line)
        tick = now()
        if text in {'[Start talking]', '[Stop talking]'}:
            self.last_status = text
            self.diag.update(status=text)
        if text.startswith('<< '):
            self.diag.update(last_irc_activity=tick)
        low = text.lower()
        if '[channel] joined ' in low:
            self.last_join_seen = time.monotonic()
        if '[connect]' in low and 'waiting up to' not in low:
            self.last_network_seen = time.monotonic()
        if 'h-key' in low or 'identity wait' in low:
            self.last_identify_attention = time.monotonic()
        if '[channel]' in low and 'no human activity' in low:
            self.diag.add({'type': 'no_human_activity', 'message': text})
        if any(k in low for k in ('[network]', '[read]', '[tls]', 'timed out', 'error', 'failed')):
            self.diag.add({'type': 'runtime_log', 'message': text}, severity='warning')

    def replaced_by_new_instance(self):
        self.diag.add({'type': 'instance_replaced', 'message': 'Another localchat instance is now running'})
        self.request_shutdown()

    def current_snapshot(self):
        st = self.client.state
        return {
            'running': not self.shutdown_event.is_set(),
            'bbs_connected': self.diag.current.get('bbs_connected', False),
            'irc_connected': bool(st.sock and not st.stop.is_set() and not st.connection_failed.is_set()),
            'network': st.net.get('name') if st.net else None,
            'channel': st.current_channel,
            'status': self.last_status,
            'user_suspended': self.client.user_suspended,
            'authenticated': bool(st.authenticated.is_set()),
            'irc_registered': bool(st.registered.is_set()),
            'last_irc_activity': self.diag.current.get('last_irc_activity'),
            'last_human_message': self.diag.current.get('last_human_message'),
            'last_outgoing_message': self.diag.current.get('last_outgoing_message'),
        }

    def status_line(self):
        return self.last_status

    def queue_message(self, message):
        message = str(message).rstrip('\r\n')
        if not message:
            return False, 'ERROR empty message'
        ok = self.client.send_message(self.client.state.current_channel, message)
        if ok:
            self.diag.update(last_outgoing_message=now())
            self.diag.add({'type': 'bbs_message_queued', 'characters': len(message)})
            return True, 'QUEUED'
        return False, 'ERROR message rejected'

    def on_human_message_poll(self):
        # localtalk.json is authoritative for human messages. Poll its newest row
        # solely for health-state metadata; message text is never exposed on TCP.
        previous = None
        while not self.shutdown_event.wait(1.0):
            try:
                rows = json.loads(LOCAL_TALK.read_text(encoding='utf-8')) if LOCAL_TALK.exists() else []
                if rows and isinstance(rows, list):
                    newest = rows[-1]
                    marker = (newest.get('time'), newest.get('network'), newest.get('channel'), newest.get('nick'))
                    if marker != previous:
                        previous = marker
                        self.last_human_seen = time.monotonic()
                        self.diag.update(last_human_message=newest.get('time'))
            except Exception as exc:
                self.diag.add({'type': 'localtalk_read_error', 'error': str(exc)}, severity='warning')

    def health_poll(self):
        started = time.monotonic()
        warned_no_server = False
        warned_no_channel = False
        while not self.shutdown_event.wait(2.0):
            snap = self.current_snapshot()
            self.diag.update(**snap)
            elapsed = time.monotonic() - started
            # These are health warnings, not fatal errors. They make "nothing ever
            # happened" diagnosable without requiring the old IRC log GUI.
            if elapsed >= 180 and self.last_network_seen == 0.0 and not self.client.user_suspended and not warned_no_server:
                warned_no_server = True
                self.diag.add({'type': 'no_irc_server_connection', 'waited_seconds': int(elapsed)}, severity='warning')
            if elapsed >= 300 and self.last_join_seen == 0.0 and not self.client.user_suspended and not warned_no_channel:
                warned_no_channel = True
                self.diag.add({'type': 'no_channel_join', 'waited_seconds': int(elapsed)}, severity='warning')
            st = self.client.state
            if st.identity_attention.is_set() and not st.authenticated.is_set() and self.last_identify_attention:
                if time.monotonic() - self.last_identify_attention > 300:
                    self.diag.add({'type': 'authentication_still_pending',
                                   'network': st.net.get('name') if st.net else None,
                                   'waited_seconds': 300}, severity='warning')
                    self.last_identify_attention = time.monotonic()

    def request_shutdown(self):
        if self.shutdown_event.is_set():
            return
        self.shutdown_event.set()
        try:
            self.client.stop_rotation()
        except Exception:
            pass
        if self.server is not None:
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def run(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        self.client.ada('startup')
        self.client.start_rotation()
        self.diag.add({'type': 'localchat_started', 'host': CONTROL_HOST, 'port': CONTROL_PORT})
        threading.Thread(target=self.health_poll, daemon=True, name='localchat-health').start()
        threading.Thread(target=self.on_human_message_poll, daemon=True, name='localchat-human-state').start()
        daemon = self

        class Handler(socketserver.StreamRequestHandler):
            def setup(self):
                super().setup()
                daemon.diag.update(bbs_connected=True)
                daemon.diag.add({'type': 'bbs_connected', 'peer': self.client_address[0]})

            def finish(self):
                try:
                    super().finish()
                finally:
                    daemon.diag.update(bbs_connected=False)
                    daemon.diag.add({'type': 'bbs_disconnected', 'peer': self.client_address[0]})

            def handle(self):
                self.wfile.write(b'LOCALCHAT READY\n')
                self.wfile.flush()
                while not daemon.shutdown_event.is_set():
                    raw = self.rfile.readline(65536)
                    if not raw:
                        break
                    line = raw.decode('utf-8', 'replace').rstrip('\r\n')
                    if not line:
                        continue
                    upper = line.upper()
                    if upper == 'PING':
                        reply = 'PONG'
                    elif upper == 'STATUS':
                        reply = daemon.status_line()
                    elif upper == 'HEALTH':
                        snap = daemon.current_snapshot()
                        fields = [
                            f"STATUS {snap['status']}",
                            f"RUNNING {1 if snap['running'] else 0}",
                            f"IRC_CONNECTED {1 if snap['irc_connected'] else 0}",
                            f"USER_SUSPENDED {1 if snap['user_suspended'] else 0}",
                            f"NETWORK {snap['network'] or '-'}",
                            f"CHANNEL {snap['channel'] or '-'}",
                            f"AUTHENTICATED {1 if snap['authenticated'] else 0}",
                            '.',
                        ]
                        reply = '\n'.join(fields)
                    elif upper == 'START':
                        daemon.client.start_rotation()
                        reply = 'OK'
                    elif upper == 'STOP':
                        daemon.client.stop_rotation()
                        reply = 'OK'
                    elif upper == 'SHUTDOWN':
                        reply = 'OK shutting down'
                        self.wfile.write((reply + '\n').encode())
                        self.wfile.flush()
                        daemon.diag.add({'type': 'bbs_shutdown_requested'})
                        daemon.request_shutdown()
                        return
                    elif upper.startswith('SEND '):
                        _, reply = daemon.queue_message(line[5:])
                    else:
                        reply = 'ERROR unknown command'
                    self.wfile.write((reply + '\n').encode('utf-8', 'replace'))
                    self.wfile.flush()

        class ThreadingLocalServer(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        try:
            with ThreadingLocalServer((CONTROL_HOST, CONTROL_PORT), Handler) as srv:
                self.server = srv
                srv.serve_forever(poll_interval=0.5)
        except OSError as exc:
            self.diag.add({'type': 'control_listener_error', 'error': str(exc),
                           'host': CONTROL_HOST, 'port': CONTROL_PORT}, severity='error')
            raise
        finally:
            self.request_shutdown()
            self.guard.release()
            self.diag.update(running=False, irc_connected=False, channel=None, network=None)
            self.diag.add({'type': 'localchat_stopped'})


def main():
    daemon = LocalChatDaemon()
    def stop_signal(_signum, _frame):
        daemon.diag.add({'type': 'signal_shutdown'})
        daemon.request_shutdown()
    signal.signal(signal.SIGTERM, stop_signal)
    signal.signal(signal.SIGINT, stop_signal)
    daemon.run()


if __name__ == '__main__':
    main()
