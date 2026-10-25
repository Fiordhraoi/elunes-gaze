#!/usr/bin/env python3
"""SPDX-License-Identifier: GPL-3.0-only. Offline PNG/image decoder; no screen capture."""
import argparse
import json
import sys
from pathlib import Path
from PIL import Image

LAYOUTS = {"slim": (16, 256), "fat": (32, 128)}
PALETTE = [(255 * ((i >> 2) & 1), 255 * ((i >> 1) & 1), 255 * (i & 1)) for i in range(8)]


def checksum(data):
    a = b = 0
    for value in data:
        a = (a + value) % 255
        b = (b + a) % 255
    return (b << 8) | a


def markers(columns):
    return {columns - 2: 7, columns - 1: 5, 2 * columns - 2: 3, 2 * columns - 1: 6}


def decode_at(image, x, y, layout):
    width, height = LAYOUTS[layout]
    if x < 0 or y < 0 or x + width > image.width or y + height > image.height:
        raise ValueError("strip extends outside image")
    columns = width // 4
    mark = markers(columns)
    data = []
    for i in range(256):
        # Sample the central 2x2 pixels of each solid 4x4 cell.
        px, py = x + (i % columns) * 4, y + (i // columns) * 4
        values = [image.getpixel((px + dx, py + dy)) for dx in (1, 2) for dy in (1, 2)]
        channels = [sum(p[c] for p in values) / 4 for c in range(3)]
        if any(80 < c < 175 for c in channels):
            raise ValueError("ambiguous cell color; use a native-size lossless screenshot")
        value = (int(channels[0] >= 128) << 2) | (int(channels[1] >= 128) << 1) | int(channels[2] >= 128)
        if i in mark:
            if value != mark[i]:
                raise ValueError("upper-right keystone does not match")
            for dx in range(4):
                for dy in range(4):
                    pixel = image.getpixel((px + dx, py + dy))
                    code = (int(pixel[0] >= 128) << 2) | (int(pixel[1] >= 128) << 1) | int(pixel[2] >= 128)
                    if code != mark[i]:
                        raise ValueError("keystone boundary is misaligned or obscured")
        else:
            data.append(value)
    acc = bits = 0
    packet = bytearray()
    for value in data:
        acc = (acc << 3) | value
        bits += 3
        if bits >= 8:
            bits -= 8
            packet.append((acc >> bits) & 255)
            acc &= (1 << bits) - 1
    if len(packet) != 94 or packet[:3] != b"EG\x01":
        raise ValueError("packet signature/version mismatch")
    kind, ident, part, count, size = packet[3], int.from_bytes(packet[4:6], "little"), packet[6], packet[7], packet[8]
    if packet[9] != 0 or not (1 <= part <= count <= 50) or size > 82 or kind > 4:
        raise ValueError("invalid packet bounds")
    if part < count and size != 82:
        raise ValueError("invalid fragment length")
    payload = bytes(packet[12:12 + size])
    if checksum(bytes(packet[:10]) + payload) != int.from_bytes(packet[10:12], "little"):
        raise ValueError("checksum mismatch; frame may be damaged or captured during an update")
    if any(packet[12 + size:]) or acc != 0:
        raise ValueError("nonzero padding")
    return {"layout": layout, "x": x, "y": y, "kind": kind, "id": ident,
            "part": part, "count": count, "payload": payload}


def find_strip(image, layout=None):
    # Threshold only for marker search. decode_at validates original cell colors and checksum.
    binary = image.point(lambda value: 255 if value >= 128 else 0).tobytes()
    stride = image.width * 3
    pattern = bytes(PALETTE[7]) * 4 + bytes(PALETTE[5]) * 4
    seen = set()
    for row in range(image.height):
        line = binary[row * stride:(row + 1) * stride]
        offset = line.find(pattern)
        while offset != -1:
            if offset % 3 == 0:
                mx = offset // 3
                for name in ([layout] if layout else LAYOUTS):
                    for top in range(max(0, row - 3), row + 1):
                        left = mx - (LAYOUTS[name][0] - 8)
                        key = (left, top, name)
                        if key in seen:
                            continue
                        seen.add(key)
                        try:
                            return decode_at(image, left, top, name)
                        except ValueError:
                            pass
            offset = line.find(pattern, offset + 3)
    raise ValueError("no checksum-valid strip found; try --layout slim --x LEFT --y TOP. Coordinates are image pixels from the upper left")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path, help="native-size screenshots in one addon session, in capture order")
    parser.add_argument("--layout", choices=LAYOUTS)
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int)
    args = parser.parse_args()
    if (args.x is None) != (args.y is None) or (args.x is not None and args.layout is None):
        parser.error("explicit coordinates require --x, --y and --layout together")
    groups = {}
    failures = 0
    for path in args.images:
        try:
            with Image.open(path) as source:
                if source.width * source.height > 40_000_000:
                    raise ValueError("image exceeds 40 megapixel limit")
                image = source.convert("RGB")
                result = (decode_at(image, args.x, args.y, args.layout)
                          if args.x is not None else find_strip(image, args.layout))
            payload = result.pop("payload")
            print(json.dumps({"image": str(path), "checksum": "OK", **result}, ensure_ascii=False))
            key = (result["kind"], result["id"], result["count"])
            group = groups.setdefault(key, {})
            part = result["part"]
            if part in group and group[part] != payload:
                raise ValueError("conflicting duplicate; do not combine screenshots from different sessions")
            group[part] = payload
        except (OSError, ValueError) as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            failures += 1
    incomplete = False
    for (kind, ident, count), parts in groups.items():
        if len(parts) != count:
            incomplete = True
            print(json.dumps({"id": ident, "status": "INCOMPLETE", "received": sorted(parts), "needed": count}))
            continue
        try:
            text = b"".join(parts[i] for i in range(1, count + 1)).decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            print(f"Message {ident}: invalid UTF-8 payload", file=sys.stderr)
            failures += 1
            continue
        print(f"Message {ident} (kind {kind}): {text}")
    return 1 if failures else (2 if incomplete else 0)


if __name__ == "__main__":
    sys.exit(main())
