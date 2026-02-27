import os.path
import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from datetime import datetime
from threading import Thread
from typing import TypeVar, Generic, Callable, Literal
from urllib.parse import urlparse

import click
import ping3

T = TypeVar("T")
SUPPORTED_FORMATS = ("txt", "xml", "html")
TIME_FORMAT = "%d.%m.%Y at %H:%M:%S"


class OutputWriter(ABC):
    @abstractmethod
    def write_ping_result(self, host: str, ping: float, ping_time: datetime | None = None) -> None:
        ...


class OutputWriterTxt(OutputWriter):
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path

    def write_ping_result(self, host: str, ping: float, ping_time: datetime | None = None) -> None:
        if ping_time is None:
            ping_time = datetime.now()

        with open(self._file_path, "a", encoding="utf8") as f:
            f.write(f"Ping to {host!r} on {ping_time.strftime(TIME_FORMAT)} is {ping * 1000:.3f}ms\n")


class OutputWriterXml(OutputWriter):
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path

    def write_ping_result(self, host: str, ping: float, ping_time: datetime | None = None) -> None:
        if ping_time is None:
            ping_time = datetime.now()

        if os.path.exists(self._file_path):
            tree = ET.parse(self._file_path)
        else:
            tree = ET.ElementTree(ET.Element("PingResults"))

        root = tree.getroot()
        result = ET.SubElement(root, "PingResult")
        result_host = ET.SubElement(result, "Host")
        result_time = ET.SubElement(result, "Time")
        result_ping = ET.SubElement(result, "Ping")

        result_host.text = host
        result_time.text = ping_time.isoformat()
        result_ping.text = f"{ping * 1000}"

        tree.write(self._file_path)


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


def validate_format(_ctx: click.Context, option: click.Option, value: str) -> str:
    value = value.lower()
    if value not in ("txt", "xml", "html"):
        raise click.UsageError(f"\"{option.opts[0]}\" must be one of: {', '.join(SUPPORTED_FORMATS)}")
    return value


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


def _run_pings(
        hosts: list[str], count: int, interval: int, output_writer: OutputWriter | None, quiet: bool,
) -> None:
    while True:
        time_now = datetime.now()

        threads = []
        for host in hosts:
            thread = ThreadWithResult(target=_ping_thread, args=(host, count))
            thread.start()
            threads.append(thread)

        for host, thread in zip(hosts, threads):
            result = thread.join()
            if output_writer is not None:
                output_writer.write_ping_result(host, result, time_now)
            if not quiet:
                print(f"[{time_now.strftime(TIME_FORMAT)}] Ping to \"{host}\": {result*1000:.2f}ms")

        if not quiet:
            print("-" * 48)

        time.sleep(interval)


@click.command()
@click.option("--host", "-h", type=click.STRING, required=False, multiple=True)
@click.option("--hosts-file", "-f", type=click.STRING, required=False, callback=validate_hosts_args)
@click.option("--ping-count", "-c", type=click.INT, required=True, default=5, callback=validate_gte_1)
@click.option("--interval", "-i", type=click.INT, required=True, default=60, callback=validate_gte_1)
@click.option("--output", "-o", type=click.STRING, required=False)
@click.option("--output-format", "-t", type=click.STRING, required=True, default="txt", callback=validate_format)
@click.option("--quiet", "-q", is_flag=True, default=False)
def main(
        host: tuple[str] | None, hosts_file: str | None, ping_count: int, interval: int, output: str | None,
        output_format: Literal["txt", "xml", "html"], quiet: bool,
) -> None:
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

    writer = None
    if output is not None and output_format == "txt":
        writer = OutputWriterTxt(output)
    elif output is not None and output_format == "xml":
        writer = OutputWriterXml(output)

    _run_pings(hosts, ping_count, interval, writer, quiet)


if __name__ == "__main__":
    main()
