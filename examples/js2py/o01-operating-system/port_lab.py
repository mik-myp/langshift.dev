"""Bind only our loopback sockets; do not inspect or stop other listeners."""
import socket


def observe() -> list[str]:
    with socket.socket() as first:
        first.bind(("127.0.0.1", 0))
        first.listen(1)
        address = first.getsockname()
        with socket.socket() as second:
            try:
                second.bind(address)
            except OSError:
                collision = True
            else:
                collision = False
        lines = [f"listening_on_loopback={address[0] == '127.0.0.1'}",
                 f"second_bind_rejected={collision}"]
    lines.append(f"owned_socket_closed={first.fileno() == -1}")
    return lines


if __name__ == "__main__":
    print("\n".join(observe()))
