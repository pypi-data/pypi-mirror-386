import asyncio
import inspect
from concurrent.interpreters import create, create_queue
from contextlib import contextmanager
from functools import cache, wraps
from textwrap import dedent
from threading import Thread
from typing import Callable, Coroutine, Iterator, Literal, Self, assert_never, cast

from .types import Shareable

__all__ = ("InterpreterError", "RunnerError", "Runner", "get_module_info")

type ModuleInfo = tuple[Literal["module", "path"], str, str]


class InterpreterError(Exception): ...


class RunnerError(Exception): ...


class Runner:
    def __init__(self, *, workers: int) -> None:
        self._tasks = create_queue()
        self._results = create_queue()
        self._futures: dict[int, tuple[asyncio.Future, asyncio.AbstractEventLoop]] = {}
        self._code = dedent("""
            import importlib
            import importlib.util
            from functools import cache

            @cache
            def load_entry_point(entry_point_type, path_or_module, name):
                if entry_point_type == "module":
                    return getattr(importlib.import_module(path_or_module), name)

                elif entry_point_type == "path":
                    spec = importlib.util.spec_from_file_location("my_module", path_or_module)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return getattr(module, name)

                else:
                    assert False

            while True:
                match tasks.get():
                    case None:
                        break
                    case id, entry_point_type, module, name, args, kwargs:
                        try:
                            entry_point = load_entry_point(entry_point_type, module, name)
                            res = entry_point(*args, **dict(kwargs))
                        except Exception as e:
                            results.put((id, False, repr(e)))
                        else:
                            results.put((id, True, res))
        """)
        self.workers = workers
        self.threads = []

    def _worker(self) -> None:
        interp = create()
        interp.prepare_main(tasks=self._tasks, results=self._results)
        interp.exec(self._code)
        interp.close()

    @contextmanager
    def start(self) -> Iterator[Self]:
        """Start the runner in a `with` block.

        This will create the workers eagerly.
        """
        coordinator = Thread(target=self._coordinator, daemon=True)
        workers = [Thread(target=self._worker, daemon=True) for _ in range(self.workers)]
        coordinator.start()
        for worker in workers:
            worker.start()

        try:
            yield self
        finally:
            # Signal to the workers
            for _ in range(self.workers):
                self._tasks.put(None)

            # Wait for workers to exit
            for worker in workers:
                worker.join()

            # Signal to the coordinator
            self._results.put(None)

            # Wait for coordinator to exit
            coordinator.join()

    def _coordinator(self) -> None:
        while True:
            match self._results.get():
                case None:
                    # Interpreter closed
                    return
                case int(i), False, str(reason):
                    future, loop = self._futures.pop(i)
                    loop.call_soon_threadsafe(future.set_exception, InterpreterError(reason))
                case int(i), True, result:
                    future, loop = self._futures.pop(i)
                    loop.call_soon_threadsafe(future.set_result, result)
                case other:
                    raise InterpreterError("Unexpected queue value: ", other)

    async def run[**P, R](self, fn: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """Run a function in a subinterpreter.

        The function must be:
        - Importable from the top level
        - Ran with only `Shareable` argument types.
        - Returns only `Shareable` argument types.
        """
        return cast(
            R,
            await self.run_module_function(
                get_module_info(fn),
                *cast(tuple[Shareable], args),
                **kwargs,
            ),
        )

    def wrap[**P, R](self, fn: Callable[P, R]) -> Callable[P, Coroutine[None, None, R]]:
        """Wrap a function returning an async function executing in a subinterpreter.

        Function must follow the same rules as defined in `Runner.run`
        """
        module_info = get_module_info(fn)

        @wraps(fn)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            return cast(
                R,
                await self.run_module_function(
                    module_info, *cast(tuple[Shareable], args), **kwargs
                ),
            )

        return wrapped

    async def run_module_function(
        self,
        module_info: ModuleInfo,
        *args: Shareable,
        **kwargs: Shareable,
    ) -> object:
        future = asyncio.Future()
        id_ = id(future)
        self._futures[id_] = future, asyncio.get_running_loop()
        self._tasks.put((id_, *module_info, args, tuple(kwargs.items())))
        return await future


@cache
def get_module_info(fn: Callable) -> ModuleInfo:
    match fn.__module__, fn.__name__:
        case None, name:
            raise RunnerError(f"{fn} is not a top level function")
        case "__main__", name:
            return "path", inspect.getfile(fn), name
        case module, name:
            return "module", module, name

        case other:
            assert_never(other)
