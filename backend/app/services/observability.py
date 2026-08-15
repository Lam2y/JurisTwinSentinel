from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import RLock
from time import monotonic, time


@dataclass
class RouteStat:
    count: int = 0
    errors: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0


class RuntimeTelemetry:
    """Small in-process telemetry layer for finals/local deployment.

    It deliberately avoids an external monitoring dependency so the demo remains offline-safe,
    while exposing the same operational signals an enterprise deployment would export to
    Prometheus/OpenTelemetry.
    """
    def __init__(self):
        self.started_at = time()
        self._lock = RLock()
        self._routes: dict[str, RouteStat] = defaultdict(RouteStat)
        self._latencies = deque(maxlen=2000)
        self._status = defaultdict(int)
        self._recent_errors = deque(maxlen=25)

    def record(self, method: str, path: str, status: int, latency_ms: float, request_id: str | None = None):
        # Collapse IDs to avoid unbounded route cardinality in a demo telemetry store.
        route = self._normalize(path)
        key = f"{method.upper()} {route}"
        with self._lock:
            s = self._routes[key]
            s.count += 1
            s.total_ms += latency_ms
            s.max_ms = max(s.max_ms, latency_ms)
            if status >= 400:
                s.errors += 1
                self._recent_errors.append({"route": key, "status": status, "request_id": request_id, "latency_ms": round(latency_ms, 2)})
            self._status[str(status)] += 1
            self._latencies.append(latency_ms)

    @staticmethod
    def _normalize(path: str) -> str:
        parts = path.strip('/').split('/') if path.strip('/') else []
        out = []
        for p in parts:
            low = p.lower()
            dynamic = (
                low.startswith(('cf-', 'jt-', 'sim-', 'apr-', 'lc-', 'ev-', 'sec-'))
                or (len(p) >= 16 and all(c in '0123456789abcdefABCDEF-' for c in p))
            )
            out.append('{id}' if dynamic else p)
        return '/' + '/'.join(out)

    def snapshot(self) -> dict:
        with self._lock:
            lat = sorted(self._latencies)
            def pct(p):
                if not lat:
                    return 0.0
                idx = min(len(lat)-1, max(0, int(round((len(lat)-1)*p))))
                return round(lat[idx], 2)
            routes = []
            for key, s in sorted(self._routes.items(), key=lambda x: x[1].count, reverse=True)[:20]:
                routes.append({
                    "route": key,
                    "requests": s.count,
                    "errors": s.errors,
                    "error_rate_pct": round(100*s.errors/max(1, s.count), 2),
                    "avg_ms": round(s.total_ms/max(1, s.count), 2),
                    "max_ms": round(s.max_ms, 2),
                })
            total = sum(self._status.values())
            errors = sum(v for k, v in self._status.items() if int(k) >= 400)
            return {
                "uptime_seconds": round(time()-self.started_at, 1),
                "requests": total,
                "errors": errors,
                "success_rate_pct": round(100*(total-errors)/max(1,total), 2),
                "latency_ms": {"p50": pct(.50), "p95": pct(.95), "p99": pct(.99)},
                "status_codes": dict(self._status),
                "top_routes": routes,
                "recent_errors": list(self._recent_errors),
                "export_note": "Offline finals telemetry; production adapter target: OpenTelemetry/Prometheus.",
            }


class SlidingWindowRateLimiter:
    def __init__(self):
        self._lock = RLock()
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        now = monotonic()
        cutoff = now - window_seconds
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= limit:
                retry = max(1, int(window_seconds - (now-q[0]))) if q else window_seconds
                return False, retry
            q.append(now)
            return True, 0


telemetry = RuntimeTelemetry()
rate_limiter = SlidingWindowRateLimiter()
