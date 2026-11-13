"""Concurrency acceptance gate for scripts/serve_tiles.py.

Fires a 12-thread burst of tile requests across dates/layers against a live
server and asserts every response is a valid PNG (or an image-safe 404
transparent body), the process stays alive, and a subsequent request still
succeeds. This is the gate that decides whether the per-handle-lock variant
of serve_tiles.py ships or the documented global-render-lock fallback is
needed (wire-platform-to-real-data task 1.3 / decision 1).

Usage:
    python scripts/test_tile_concurrency.py --port 8765 [--rounds 3]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import random
import sys
import urllib.error
import urllib.request
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def http_get(url: str, timeout: float = 60.0) -> tuple[int, str, bytes]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--rounds", type=int, default=3, help="burst rounds")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    base = f"http://{args.host}:{args.port}"
    index = json.loads(urllib.request.urlopen(f"{base}/scenes", timeout=30).read())
    scenes = [s for s in index["scenes"] if s.get("has_rgb") and s.get("has_ndvi")]
    if not scenes:
        print("FAIL: no scenes with both rgb and ndvi in /scenes index")
        return 1

    # Scene centers as slippy tiles at a zoom inside the served 8-14 range.
    def tile_for(scene: dict, z: int) -> tuple[int, int]:
        lon = (scene["bounds"][0] + scene["bounds"][2]) / 2
        lat = (scene["bounds"][1] + scene["bounds"][3]) / 2
        n = 2**z
        x = int((lon + 180.0) / 360.0 * n)
        import math

        y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)
        return x, y

    rng = random.Random(20261107)
    urls: list[str] = []
    for _ in range(args.rounds):
        for scene in rng.sample(scenes, min(len(scenes), 6)):
            z = rng.randint(9, 14)
            x, y = tile_for(scene, z)
            layer = rng.choice(("rgb", "ndvi"))
            urls.append(f"{base}/tiles/{scene['date']}/{layer}/{z}/{x}/{y}.png")

    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {u: pool.submit(http_get, u) for u in urls}
        for url, fut in futures.items():
            try:
                status, ctype, body = fut.result()
            except Exception as exc:  # connection reset / refused = process crash
                failures.append(f"{url}: transport failure {type(exc).__name__}: {exc}")
                continue
            ok_png = body.startswith(PNG_MAGIC)
            ok_err = status in (404, 500) and ctype == "image/png" and ok_png
            if status == 200 and ctype == "image/png" and ok_png:
                continue
            if ok_err:
                continue
            failures.append(f"{url}: status={status} ctype={ctype} png={ok_png} len={len(body)}")

    # The process must still be alive and serving after the burst.
    try:
        status, ctype, body = http_get(f"{base}/scenes")
        post_ok = status == 200 and ctype == "application/json"
    except Exception as exc:
        post_ok = False
        failures.append(f"post-burst /scenes failed: {type(exc).__name__}: {exc}")

    total = len(urls)
    print(f"burst: {total} requests, {total - len(failures)} ok, {len(failures)} failures")
    for f in failures[:10]:
        print("  FAIL:", f)
    print("post-burst /scenes:", "OK" if post_ok else "FAIL")
    if not failures and post_ok:
        print("PASS: server survived the burst, all responses image-safe")
        return 0
    print("FAIL: server did not survive or returned non-image errors")
    return 1


if __name__ == "__main__":
    sys.exit(main())
