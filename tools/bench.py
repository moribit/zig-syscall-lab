#!/usr/bin/env python3
"""Closed-loop TCP echo load generator. Run server separately; stdlib only."""
import argparse
import concurrent.futures
import json
import math
import socket
import time


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def worker(args):
    latencies = []
    errors = 0
    payload = b"x" * args.bytes
    try:
        with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
            sock.settimeout(args.timeout)
            for index in range(args.warmup + args.requests):
                start = time.perf_counter_ns()
                sock.sendall(payload)
                remaining = len(payload)
                while remaining:
                    part = sock.recv(remaining)
                    if not part:
                        raise OSError("unexpected EOF")
                    if part != b"x" * len(part):
                        raise OSError("echo mismatch")
                    remaining -= len(part)
                if index >= args.warmup:
                    latencies.append((time.perf_counter_ns() - start) / 1e6)
    except (OSError, TimeoutError):
        errors = args.requests - len(latencies)
    return latencies, errors


def percentile(values, p):
    if not values:
        return None
    return values[max(0, math.ceil(len(values) * p) - 1)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--clients", type=positive, default=10)
    parser.add_argument("--requests", type=positive, default=1000)
    parser.add_argument("--bytes", type=positive, default=64)
    parser.add_argument("--warmup", type=positive, default=20)
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.clients) as pool:
        results = list(pool.map(lambda _: worker(args), range(args.clients)))
    elapsed = time.perf_counter() - start
    samples = sorted(v for values, _ in results for v in values)
    errors = sum(n for _, n in results)
    print(json.dumps({
        "clients": args.clients, "payload_bytes": args.bytes,
        "attempted_measured_requests": args.clients * args.requests,
        "success": len(samples), "errors": errors, "elapsed_seconds": elapsed,
        "requests_per_second_including_setup_and_warmup": len(samples) / elapsed,
        "payload_bytes_per_second_one_direction": len(samples) * args.bytes / elapsed,
        "latency_ms": {"p50": percentile(samples, .5),
                       "p95": percentile(samples, .95), "p99": percentile(samples, .99)},
        "model": "closed-loop; latency excludes connection setup and warmup; throughput denominator includes them"
    }, indent=2))
    raise SystemExit(1 if errors else 0)
