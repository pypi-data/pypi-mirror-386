from __future__ import annotations

import queue
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, Protocol

from pycoro import scheduler

if TYPE_CHECKING:
    from pycoro.io import io


# Coroutine
class Coroutine[T, TNext, TReturn](Protocol):
    def time(self) -> int: ...
    def set(self, key: str, value: Any) -> None: ...
    def get(self, key: str) -> Any: ...
    def resources(self) -> dict[str, Any]: ...
    def emit_and_wait(self, e: _Emit[T, TNext, TReturn]) -> None: ...
    def executor(self) -> ThreadPoolExecutor: ...


type CoroutineFunc[T, TNext, TReturn] = Callable[[Coroutine[T, TNext, TReturn]], TReturn]


@dataclass(frozen=True)
class _Emit[T, TNext, TReturn]:
    value: T | None = None
    promise: Future[TNext] | None = None
    spawn: scheduler.Coroutine[T, TNext] | None = None
    wait: Future[Any] | None = None
    done: bool = False


class _Coroutine[T, TNext, TReturn]:
    def __init__(
        self,
        f: CoroutineFunc[T, TNext, TReturn],
        r: dict[str, Any],
        executor: ThreadPoolExecutor,
    ) -> None:
        self._f: Final = f
        self._r: Final = r
        self._executor: Final = executor
        self.p: Final = Future[TReturn]()
        self._t: int

        self._c_i: Final = queue.Queue[Any]()
        self._c_o: Final = queue.Queue[_Emit[T, TNext, TReturn]]()

        _ = self._executor.submit(self._worker)

    def _worker(self) -> None:
        self._c_i.get()

        try:
            self.p.set_result(self._f(self))
        except Exception as e:
            self.p.set_exception(e)

        self._c_i.shutdown()

        self._c_o.put(_Emit[T, TNext, TReturn](done=True))
        self._c_o.shutdown()

    def resume(
        self,
    ) -> tuple[
        T | None,
        Future[TNext] | None,
        scheduler.Coroutine[T, TNext] | None,
        Future[Any] | None,
        bool,
    ]:
        self._c_i.put(None)
        o = self._c_o.get()
        return o.value, o.promise, o.spawn, o.wait, o.done

    def set_time(self, time: int) -> None:
        self._t = time

    def time(self) -> int:
        return self._t

    def set(self, key: str, value: Any) -> None:
        self._r[key] = value

    def get(self, key: str) -> Any:
        return self._r[key]

    def resources(self) -> dict[str, Any]:
        return self._r

    def emit_and_wait(self, e: _Emit[T, TNext, TReturn]) -> None:
        self._c_o.put(e)
        self._c_i.get()

    def executor(self) -> ThreadPoolExecutor:
        return self._executor


# Public API


class _Scheduler[I, O](Protocol):
    def add(self, c: scheduler.Coroutine[I, O]) -> bool: ...
    def run_until_blocked(self, time: int) -> None: ...
    def shutdown(self) -> None: ...
    def size(self) -> int: ...
    def tick(self, time: int) -> None: ...
    def step(self, time: int) -> bool: ...
    def executor(self) -> ThreadPoolExecutor: ...


class Scheduler[I, O]:
    def __init__(self, io: io.IO[I, O], size: int) -> None:
        self._executor: Final = ThreadPoolExecutor(max_workers=size)
        self._s: Final = scheduler.Scheduler[I, O](io, size)

    def add(self, c: scheduler.Coroutine[I, O]) -> bool:
        return self._s.add(c)

    def run_until_blocked(self, time: int) -> None:
        return self._s.run_until_blocked(time)

    def shutdown(self) -> None:
        self._s.shutdown()
        self._executor.shutdown(wait=True)

    def size(self) -> int:
        return self._s.size()

    def tick(self, time: int) -> None:
        return self._s.tick(time)

    def step(self, time: int) -> bool:
        return self._s.step(time)

    def executor(self) -> ThreadPoolExecutor:
        return self._executor


def add[T, TNext, TReturn](
    s: _Scheduler[T, TNext], f: CoroutineFunc[T, TNext, TReturn]
) -> Future[TReturn] | None:
    coroutine = _Coroutine(f, {}, s.executor())
    if s.add(coroutine):
        return coroutine.p
    return None


def emit[T, TNext, TReturn](c: Coroutine[T, TNext, TReturn], v: T) -> Future[TNext]:
    p = Future[TNext]()
    c.emit_and_wait(_Emit[T, TNext, TReturn](value=v, promise=p))
    return p


def spawn[T, TNext, TReturn, R](
    c: Coroutine[T, TNext, TReturn], f: CoroutineFunc[T, TNext, R]
) -> Future[R]:
    coroutine = _Coroutine(f, c.resources(), c.executor())
    c.emit_and_wait(_Emit[T, TNext, TReturn](spawn=coroutine))
    return coroutine.p


def wait[T, TNext, TReturn, P](c: Coroutine[T, TNext, TReturn], p: Future[P]) -> P:
    if not p.done():
        c.emit_and_wait(_Emit[T, TNext, TReturn](wait=p))
    assert p.done(), "promise must be completed"
    return p.result()


def emit_and_wait[T, TNext, TReturn](c: Coroutine[T, TNext, TReturn], v: T) -> TNext | Exception:
    return wait(c, emit(c, v))


def spawn_and_wait[T, TNext, TReturn, R](
    c: Coroutine[T, TNext, TReturn], f: CoroutineFunc[T, TNext, R]
) -> R | Exception:
    return wait(c, spawn(c, f))
