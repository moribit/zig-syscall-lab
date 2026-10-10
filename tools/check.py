#!/usr/bin/env python3
"""Black-box checks; contains no learner implementation. Python stdlib only."""
import argparse
import concurrent.futures
import socket
import subprocess
import tempfile
from pathlib import Path


def receive(sock, count):
    data = bytearray()
    while len(data) < count:
        part = sock.recv(min(65536, count - len(data)))
        if not part:
            raise AssertionError(f"unexpected EOF: {len(data)}/{count}")
        data.extend(part)
    return bytes(data)


def connect(args):
    sock = socket.create_connection((args.host, args.port), timeout=args.timeout)
    sock.settimeout(args.timeout)
    return sock


def echo(args, index=0):
    # Chunked full-duplex transfer exercises stream boundaries without relying
    # on the kernel to return a particular partial-write length.
    payload = bytes(range(256)) * 257 + bytes([index % 256])
    with connect(args) as sock:
        for start in range(0, len(payload), 997):
            chunk = payload[start:start + 997]
            sock.sendall(chunk)
            assert receive(sock, len(chunk)) == chunk, "echo bytes differ"
        sock.shutdown(socket.SHUT_WR)
        assert sock.recv(1) == b"", "expected graceful EOF"


def run(args):
    if args.mode in ("cat", "cp"):
        if not args.binary:
            raise ValueError("--binary is required for file checks")
        binary = str(Path(args.binary).resolve())
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "source"
            dst = Path(directory) / "destination"
            for payload in (b"", b"a", bytes(range(256)) * 8193):
                src.write_bytes(payload)
                dst.write_bytes(b"old destination" * 20)
                command = [binary, args.mode, str(src)]
                if args.mode == "cp":
                    command.append(str(dst))
                result = subprocess.run(command, capture_output=True, timeout=args.timeout)
                assert result.returncode == 0, result.stderr.decode(errors="replace")
                actual = result.stdout if args.mode == "cat" else dst.read_bytes()
                assert actual == payload, "file bytes differ (or destination not truncated)"
            result = subprocess.run([binary, "cat", str(src) + ".missing"],
                                    capture_output=True, timeout=args.timeout)
            assert result.returncode != 0, "missing input must fail"
        return
    if args.mode == "echo":
        if args.multi:
            with connect(args) as idle:
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    list(pool.map(lambda i: echo(args, i), range(4)))
                # An idle first client must not prevent active clients' progress.
                idle.shutdown(socket.SHUT_WR)
        else:
            echo(args)
        echo(args, 17)  # reconnect after graceful close
        return
    if args.mode == "chat":
        with connect(args) as a, connect(args) as b, connect(args) as c:
            # No sleep race: use a round trip from each client as a readiness barrier.
            c.sendall(b"ready-c\n")
            assert receive(a, 8) == b"ready-c\n"
            assert receive(b, 8) == b"ready-c\n"
            b.sendall(b"ready-b\n")
            assert receive(a, 8) == b"ready-b\n"
            assert receive(c, 8) == b"ready-b\n"
            a.sendall(b"hel")
            a.sendall(b"lo\nsecond\n")
            expected = b"hello\nsecond\n"
            assert receive(b, len(expected)) == expected
            assert receive(c, len(expected)) == expected
        return
    raise ValueError(args.mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("cat", "cp", "echo", "chat"))
    parser.add_argument("--binary")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--multi", action="store_true")
    args = parser.parse_args()
    try:
        run(args)
    except (AssertionError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"FAIL: {error}\n")
    print("PASS: black-box contract (not all chapter completion criteria)")
