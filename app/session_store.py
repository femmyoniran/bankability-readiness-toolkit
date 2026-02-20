"""
Server-side session store.

Flask's default cookie-based session has a 4KB browser limit.
Project data and assessment results exceed this limit, so we store
them server-side keyed by a session identifier stored in the cookie.
"""

import uuid
from flask import session

_store = {}


def _get_sid():
    sid = session.get("_sid")
    if not sid:
        sid = str(uuid.uuid4())
        session["_sid"] = sid
    return sid


def store_set(key, value):
    sid = _get_sid()
    if sid not in _store:
        _store[sid] = {}
    _store[sid][key] = value


def store_get(key, default=None):
    sid = session.get("_sid")
    if not sid or sid not in _store:
        return default
    return _store[sid].get(key, default)


def store_clear():
    sid = session.get("_sid")
    if sid and sid in _store:
        del _store[sid]
