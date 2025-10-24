import asyncio
import hashlib
import inspect
import json
import logging
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .cache import AbstractCache
from .decision import Decision
from .helpers import maybe_await
from .model import Action, Context, Resource, Subject
from .obligations import BasicObligationChecker
from .policy import decide as decide_policy
from .policyset import decide as decide_policyset
from .ports import (
    DecisionLogSink,
    MetricsSink,
    ObligationChecker,
    RelationshipChecker,
    RoleResolver,
)
from .relctx import EVAL_LOOP, REL_CHECKER, REL_LOCAL_CACHE

try:
    # optional compile step to speed up decision making
    from .compiler import compile as compile_policy
except Exception:  # pragma: no cover - compiler is optional
    compile_policy = None  # type: ignore[assignment]

logger = logging.getLogger("rbacx.engine")


def _now() -> float:
    """Monotonic time for durations."""
    return time.perf_counter()


class Guard:
    """Policy evaluation engine.

    Holds a policy or a policy set and evaluates access decisions.

    Design:
      - Single async core `_evaluate_core_async` (one source of truth).
      - Sync API wraps the async core; if a loop is already running, uses a helper thread.
      - DI (resolver/obligations/metrics/logger) can be sync or async; both supported via `maybe_await`.
      - CPU-bound evaluation is offloaded to a thread via `asyncio.to_thread`.
      - On init we ensure a current event loop exists in this thread so
        legacy tests using `asyncio.get_event_loop().run_until_complete(...)`
        don’t crash on Python 3.12+.
    """

    def __init__(
        self,
        policy: dict[str, Any],
        *,
        logger_sink: DecisionLogSink | None = None,
        metrics: MetricsSink | None = None,
        obligation_checker: ObligationChecker | None = None,
        role_resolver: RoleResolver | None = None,
        relationship_checker: RelationshipChecker | None = None,
        cache: AbstractCache | None = None,
        cache_ttl: int | None = 300,
        strict_types: bool = False,
    ) -> None:
        self.policy: dict[str, Any] = policy
        self.logger_sink = logger_sink
        self.metrics = metrics
        self.obligations: ObligationChecker = obligation_checker or BasicObligationChecker()
        self.role_resolver = role_resolver
        # Optional decision cache (per-Guard instance by default)
        self.cache: AbstractCache | None = cache
        self.cache_ttl: int | None = cache_ttl
        self.policy_etag: str | None = None
        self._compiled: Callable[[dict[str, Any]], dict[str, Any]] | None = None
        self.strict_types: bool = bool(strict_types)
        self.relationship_checker = relationship_checker

        # Provide a "current" loop if missing (helps tests on Py3.12+).
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            try:
                asyncio.get_event_loop()
            except RuntimeError:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                except Exception:  # pragma: no cover
                    logger.debug(
                        "Guard.__init__: failed to create or set a new event loop", exc_info=True
                    )

        self._recompute_etag()

    # ---------------------------------------------------------------- set/update

    def set_policy(self, policy: dict[str, Any]) -> None:
        """Replace policy/policyset."""
        self.policy = policy
        self._recompute_etag()
        # Invalidate cache entirely; etag changes will naturally change keys,
        # but clearing avoids memory growth and stale entries.
        self.clear_cache()

    def update_policy(self, policy: dict[str, Any]) -> None:
        """Alias kept for backward-compatibility."""
        self.set_policy(policy)

    # ------------------------------ caching helpers

    @staticmethod
    def _normalize_env_for_cache(env: dict[str, Any]) -> str:
        """Return a deterministic JSON string for cache key construction.

        - sort_keys=True ensures a stable order
        - separators reduce size
        - default=str avoids TypeErrors for non-JSON types by stringifying them.
        - ensure_ascii=False preserves unicode while keeping key stable
        Security: Do NOT put secrets into keys for shared caches. The default
        in-memory cache is per-process and per-Guard; for external caches,
        ensure transport-level protections.
        """
        try:
            return json.dumps(
                env, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False
            )
        except Exception:
            # As a last resort, fall back to repr which is deterministic for basic containers.
            return repr(env)

    def _cache_key(self, env: dict[str, Any]) -> str | None:
        etag = getattr(self, "policy_etag", None)
        if not etag:
            return None
        return f"{etag}:{self._normalize_env_for_cache(env)}"

    # ---------------------------------------------------------------- decision core (async only)

    async def _decide_async(self, env: dict[str, Any]) -> dict[str, Any]:
        """
        Async decision that keeps the event loop responsive:
        compiled/policy/policyset functions are sync -> offload via to_thread.
        """
        fn = self._compiled
        loop = asyncio.get_running_loop()
        token = EVAL_LOOP.set(loop)
        try:
            # compiled (if available)
            try:
                if fn is not None:
                    return await asyncio.to_thread(fn, env)
            except Exception:  # pragma: no cover
                logger.exception("RBACX: compiled decision failed; falling back")

            # policyset vs single policy
            if "policies" in self.policy:
                return await asyncio.to_thread(decide_policyset, self.policy, env)

            return await asyncio.to_thread(decide_policy, self.policy, env)
        finally:
            EVAL_LOOP.reset(token)

    # ---------------------------------------------------------------- evaluation core (single source of truth)

    async def _evaluate_core_async(
        self,
        subject: Subject,
        action: Action,
        resource: Resource,
        context: Context | None,
    ) -> Decision:
        start = _now()

        # Build env (resolver may be sync or async)
        roles: list[str] = list(subject.roles or [])
        if self.role_resolver is not None:
            try:
                roles = await maybe_await(self.role_resolver.expand(roles))
            except Exception:
                logger.exception("RBACX: role resolver failed", exc_info=True)
        env: dict[str, Any] = {
            "subject": {"id": subject.id, "roles": roles, "attrs": dict(subject.attrs or {})},
            "action": action.name,
            "resource": {
                "type": resource.type,
                "id": resource.id,
                "attrs": dict(resource.attrs or {}),
            },
            "context": dict(getattr(context, "attrs", {}) or {}),
        }

        if self.strict_types:
            env["__strict_types__"] = True

        raw = None
        cache = getattr(self, "cache", None)
        key: str | None = None

        if cache is not None:
            try:
                key = self._cache_key(env)
                if key:
                    cached = cache.get(key)
                    if cached is not None:
                        raw = cached
            except Exception:  # pragma: no cover
                logger.exception("RBACX: cache.get failed")

        if raw is None:
            # Make ReBAC provider and a per-decision local cache available to policy code
            _t1 = REL_CHECKER.set(self.relationship_checker)
            _t2 = REL_LOCAL_CACHE.set({})
            try:
                raw = await self._decide_async(env)
            finally:
                REL_CHECKER.reset(_t1)
                REL_LOCAL_CACHE.reset(_t2)

            if cache is not None:
                try:
                    if key:
                        cache.set(key, raw, ttl=self.cache_ttl)
                except Exception:  # pragma: no cover
                    logger.exception("RBACX: cache.set failed")

        # determine effect/allowed with obligations
        decision_str = str(raw.get("decision"))
        effect = "permit" if decision_str == "permit" else "deny"
        obligations_list = list(raw.get("obligations") or [])
        challenge = raw.get("challenge")
        allowed = decision_str == "permit"

        if allowed:
            try:
                ok, ch = await maybe_await(self.obligations.check(raw, context))
                allowed = bool(ok)
                if ch is not None:
                    challenge = ch
                # Auto-deny when an obligation is not met
                if not allowed:
                    effect = "deny"
                    raw["reason"] = "obligation_failed"
            except Exception:
                # do not fail on obligation checker errors
                logger.exception("RBACX: obligation checker failed", exc_info=True)

        d = Decision(
            allowed=allowed,
            effect=effect,
            obligations=obligations_list,
            challenge=challenge,
            rule_id=raw.get("last_rule_id") or raw.get("rule_id"),
            policy_id=raw.get("policy_id"),
            reason=raw.get("reason"),
        )

        # metrics (do not use return values; conditionally await)
        if self.metrics is not None:
            labels = {"decision": d.effect}
            try:
                inc = getattr(self.metrics, "inc", None)
                if inc is not None:
                    if inspect.iscoroutinefunction(inc):
                        await inc("rbacx_decisions_total", labels)
                    else:
                        inc("rbacx_decisions_total", labels)
            except Exception:  # pragma: no cover
                logger.exception("RBACX: metrics.inc failed")
            try:
                observe = getattr(self.metrics, "observe", None)
                if observe is not None:
                    dur = max(0.0, _now() - start)
                    if inspect.iscoroutinefunction(observe):
                        await observe("rbacx_decision_seconds", dur, labels)
                    else:
                        observe("rbacx_decision_seconds", dur, labels)
            except Exception:  # pragma: no cover
                logger.exception("RBACX: metrics.observe failed")

        # logging (do not use return value; conditionally await)
        if self.logger_sink is not None:
            try:
                log = getattr(self.logger_sink, "log", None)
                if log is not None:
                    payload = {
                        "env": env,
                        "decision": d.effect,
                        "allowed": d.allowed,
                        "rule_id": d.rule_id,
                        "policy_id": d.policy_id,
                        "reason": d.reason,
                        "obligations": d.obligations,
                    }
                    if inspect.iscoroutinefunction(log):
                        await log(payload)
                    else:
                        log(payload)
            except Exception:  # pragma: no cover
                logger.exception("RBACX: decision logging failed")

        return d

    # ---------------------------------------------------------------- public APIs

    def clear_cache(self) -> None:
        """Clear the decision cache if configured.

        This is safe to call at any time. Errors are swallowed to avoid
        interfering with decision flow.
        """
        cache = getattr(self, "cache", None)
        if cache is not None:
            try:
                cache.clear()
            except Exception:  # pragma: no cover
                logger.exception("RBACX: cache.clear() failed")

    def evaluate_sync(
        self,
        subject: Subject,
        action: Action,
        resource: Resource,
        context: Context | None = None,
    ) -> Decision:
        """
        Synchronous wrapper for the async core.
        - If no running loop in this thread: use asyncio.run(...)
        - If a loop is running: run the async core in a helper thread with its own loop.
        """
        try:
            asyncio.get_running_loop()
            loop_running = True
        except RuntimeError:
            loop_running = False

        if not loop_running:
            return asyncio.run(self._evaluate_core_async(subject, action, resource, context))

        # Avoid interacting with the already running loop from sync code.
        def _runner() -> Decision:
            return asyncio.run(self._evaluate_core_async(subject, action, resource, context))

        with ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_runner)
            return fut.result()

    async def evaluate_async(
        self,
        subject: Subject,
        action: Action,
        resource: Resource,
        context: Context | None = None,
    ) -> Decision:
        """True async API for ASGI frameworks."""
        return await self._evaluate_core_async(subject, action, resource, context)

    # convenience

    def is_allowed_sync(
        self, subject: Subject, action: Action, resource: Resource, context: Context | None = None
    ) -> bool:
        d = self.evaluate_sync(subject, action, resource, context)
        return d.allowed

    async def is_allowed_async(
        self, subject: Subject, action: Action, resource: Resource, context: Context | None = None
    ) -> bool:
        d = await self.evaluate_async(subject, action, resource, context)
        return d.allowed

    # ---------------------------------------------------------------- internals

    def _recompute_etag(self) -> None:
        try:
            raw = json.dumps(self.policy, sort_keys=True).encode("utf-8")
            self.policy_etag = hashlib.sha3_256(raw).hexdigest()
        except Exception:
            self.policy_etag = None
        # compile if compiler available
        try:
            if compile_policy is not None:
                self._compiled = compile_policy(self.policy)
        except Exception:
            self._compiled = None
