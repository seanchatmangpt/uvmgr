from uvmgr.core.telemetry import span


def run(host: str, cmd: str, *_, **__):
    with span("remote.run", host=host, cmd=cmd):
        raise NotImplementedError("remote runner not implemented yet")
