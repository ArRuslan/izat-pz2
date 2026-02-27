import time
from threading import Thread
from typing import TypeVar, Generic, Callable
from urllib.parse import urlparse

import click
import ping3


def validate_hosts_args(ctx: click.Context, _: click.Option, value: str) -> str:
    host_param = ctx.params.get("host")

    if not host_param and not value:
        raise click.UsageError("either \"--host\" or \"--hosts-file\" must be specified.")
    if host_param and value:
        raise click.UsageError("only \"--host\" or \"--hosts-file\" must be specified.")

    return value


def validate_gte_1(_ctx: click.Context, option: click.Option, value: int) -> int:
    if value < 1:
        raise click.UsageError(f"\"{option.opts[0]}\" must be greater than or equal to 1")
    return value


T = TypeVar("T")


class ThreadWithResult(Thread, Generic[T]):
    __slots__ = ("result", "result_set",)

    def __init__(self, target: Callable, args: tuple, default: T | None = None) -> None:
        super().__init__(target=target, args=args)

        self.result = default
        self.result_set = False

    def run(self) -> None:
        self.result = self._target(*self._args, **self._kwargs)

    def join(self, timeout: float | None = None) -> T:
        super().join(timeout)
        return self.result


def _ping_thread(host: str, count: int) -> float:
    pings = []
    for _ in range(count):
        pings.append(ping3.ping(host))

    return sum(pings) / len(pings)


def _run_pings(hosts: list[str], count: int, interval: int) -> None:
    while True:
        threads = []
        for host in hosts:
            thread = ThreadWithResult(target=_ping_thread, args=(host, count))
            thread.start()
            threads.append(thread)

        for host, thread in zip(hosts, threads):
            result = thread.join()
            print(f"Ping to \"{host}\": {result*1000:.2f}ms")

        print("-" * 32)

        time.sleep(interval)


@click.command()
@click.option("--host", "-h", type=click.STRING, required=False, multiple=True)
@click.option("--hosts-file", "-f", type=click.STRING, required=False, callback=validate_hosts_args)
@click.option("--ping-count", "-c", type=click.INT, required=True, default=5, callback=validate_gte_1)
@click.option("--interval", "-i", type=click.INT, required=True, default=60, callback=validate_gte_1)
def main(host: tuple[str] | None, hosts_file: str | None, ping_count: int, interval: int) -> None:
    if hosts_file:
        with open(hosts_file) as f:
            host = f.read().splitlines()

    hosts = []
    for host_ in host:
        parsed = urlparse(host_)
        if not parsed.netloc:
            hosts.append(parsed.path)
        else:
            hosts.append(parsed.netloc)

    _run_pings(hosts, ping_count, interval)


if __name__ == "__main__":
    main()
