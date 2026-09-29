from __future__ import annotations

import socket


def find_free_port(host: str = "127.0.0.1") -> int:
    """Ask the OS for an unused TCP port.

    Every experiment run starts its own Flower server subprocess bound
    to `config.server_address`. That used to be hardcoded to
    "localhost:8080" everywhere, which works fine for a single person
    running one experiment at a time locally, but breaks the moment two
    experiments (from two different users, or two browser tabs) try to
    run at once: the second server subprocess fails to bind the port
    that the first one is already listening on.

    Binding to port 0 makes the OS pick a free ephemeral port for us; we
    read it back with getsockname() and immediately close the socket so
    the launcher's own subprocess can bind that same port a moment
    later. There's a small, unavoidable race — another process could in
    principle grab the port between our close() and the subprocess's
    bind() — but this is the standard "find me a free port" pattern and
    is dramatically safer than every run sharing one fixed port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]
