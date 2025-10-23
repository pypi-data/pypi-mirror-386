import sys
from importlib import import_module
from importlib.machinery import ModuleSpec
from importlib.util import find_spec, module_from_spec
from pathlib import Path

__version__ = "0.0.2.2"


async def run_with_hmr(target: str, log_level: str | None = None):
    module, attr = target.rsplit(":", 1)

    from asyncio import Event, Lock, TaskGroup
    from contextlib import contextmanager, suppress

    import mcp.server
    from fastmcp import FastMCP
    from fastmcp.server.proxy import ProxyClient
    from reactivity import async_effect, derived
    from reactivity.hmr.core import HMR_CONTEXT, AsyncReloader, _loader
    from reactivity.hmr.hooks import call_post_reload_hooks, call_pre_reload_hooks

    base_app = FastMCP(name="proxy", include_fastmcp_meta=False)

    @contextmanager
    def mount(app: FastMCP | mcp.server.FastMCP):
        base_app.mount(proxy := FastMCP.as_proxy(ProxyClient(app)), as_proxy=False)
        try:
            yield
        finally:  # unmount
            for mounted_server in list(base_app._mounted_servers):
                if mounted_server.server is proxy:
                    base_app._mounted_servers.remove(mounted_server)
                    with suppress(AttributeError):
                        base_app._tool_manager._mounted_servers.remove(mounted_server)
                        base_app._resource_manager._mounted_servers.remove(mounted_server)
                        base_app._prompt_manager._mounted_servers.remove(mounted_server)
                    break

    lock = Lock()

    async def using(app: FastMCP | mcp.server.FastMCP, stop_event: Event, finish_event: Event):
        async with lock:
            with mount(app):
                await stop_event.wait()
                finish_event.set()

    if Path(module).is_file():  # module:attr

        @derived(context=HMR_CONTEXT)
        def get_app():
            return getattr(module_from_spec(ModuleSpec("server_module", _loader, origin=module)), attr)

    else:  # path:attr

        @derived(context=HMR_CONTEXT)
        def get_app():
            return getattr(import_module(module), attr)

    stop_event: Event | None = None
    finish_event: Event = ...  # type: ignore

    @async_effect(context=HMR_CONTEXT, call_immediately=False)
    async def main():
        nonlocal stop_event, finish_event

        if stop_event is not None:
            stop_event.set()
            await finish_event.wait()

        app = get_app()

        tg.create_task(using(app, stop_event := Event(), finish_event := Event()))

    class Reloader(AsyncReloader):
        def __init__(self):
            super().__init__("")
            self.error_filter.exclude_filenames.add(__file__)

        async def __aenter__(self):
            call_pre_reload_hooks()
            try:
                await main()
            finally:
                call_post_reload_hooks()
                tg.create_task(self.start_watching())

        async def __aexit__(self, *_):
            self.stop_watching()
            main.dispose()
            if stop_event:
                stop_event.set()

    async with TaskGroup() as tg, Reloader():
        await base_app.run_stdio_async(show_banner=False, log_level=log_level)


def cli(argv: list[str] = sys.argv[1:]):
    from argparse import SUPPRESS, ArgumentParser

    parser = ArgumentParser("mcp-hmr", description="Hot Reloading for MCP Servers • Automatically reload on code changes")
    if sys.version_info >= (3, 14):
        parser.suggest_on_error = True
    parser.add_argument("target", help="The import path of the FastMCP instance. Supports module:attr and path:attr")
    parser.add_argument("-l", "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], type=str.upper, default=None)
    parser.add_argument("--version", action="version", version=f"mcp-hmr {__version__}", help=SUPPRESS)

    if not argv:
        parser.print_help()
        return

    args = parser.parse_args(argv)

    target: str = args.target

    if ":" not in target[1:-1]:
        parser.exit(1, f"The target argument must be in the format 'module:attr' (e.g. 'main:app') or 'path:attr' (e.g. './path/to/main.py:app'). Got: '{target}'")

    from asyncio import run
    from contextlib import suppress

    if (cwd := str(Path.cwd())) not in sys.path:
        sys.path.append(cwd)

    if (file := Path(module_or_path := target[: target.rindex(":")])).is_file():
        sys.path.insert(0, str(file.parent))
    elif find_spec(module_or_path) is None:
        parser.exit(1, f"The target '{module_or_path}' not found. Please provide a valid module name or a file path.")

    with suppress(KeyboardInterrupt):
        run(run_with_hmr(target, args.log_level))


if __name__ == "__main__":
    cli()
