import time

import click


def validate_hosts_args(ctx: click.Context, _: click.Option, value: str) -> str:
    host_param = ctx.params.get("host")

    if not host_param and not value:
        raise click.UsageError("Either \"--host\" or \"--hosts-file\" must be specified.")
    if host_param and value:
        raise click.UsageError("Only \"--host\" or \"--hosts-file\" must be specified.")

    return value


@click.command()
@click.option("--host", "-h", type=click.STRING, required=False, multiple=True)
@click.option("--hosts-file", "-f", type=click.STRING, required=False, callback=validate_hosts_args)
@click.option("--ping-count", "-c", type=click.INT, required=True, default=5)
@click.option("--interval", "-i", type=click.INT, required=True, default=60)
def main(host: tuple[str] | None, hosts_file: str | None, ping_count: int, interval: int) -> None:
    if hosts_file:
        with open(hosts_file) as f:
            host = f.read().splitlines()

    while True:
        for host_ in host:
            pings = []
            for _ in range(ping_count):
                ...

        time.sleep(interval)


if __name__ == "__main__":
    main()
