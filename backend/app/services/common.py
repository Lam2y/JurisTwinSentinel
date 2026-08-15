import json
from datetime import datetime, timezone


def loads(value, default=None):
    if value is None:
        return {} if default is None else default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return {} if default is None else default


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def iso(dt):
    if not dt:
        return None
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def utcnow():
    return datetime.now(timezone.utc)
