"""SPDX-License-Identifier: GPL-3.0-only. Generate known, synthetic calibration images."""
from pathlib import Path
from PIL import Image
from read_strip import PALETTE, LAYOUTS, markers, checksum

def main():
    payload = b'{"type":"sample","text":"Hello from Elunes Gaze"}'
    header = b'EG\x01\x01\x01\x00\x01\x01' + bytes([len(payload), 0])
    packet = header + checksum(header + payload).to_bytes(2, 'little') + payload + bytes(82 - len(payload))
    bits = ''.join(f'{value:08b}' for value in packet) + '0000'
    values = [int(bits[i:i+3], 2) for i in range(0, len(bits), 3)]
    folder = Path(__file__).parent / 'fixtures'
    folder.mkdir(exist_ok=True)
    for name, (width, height) in LAYOUTS.items():
        image = Image.new('RGB', (width, height))
        columns = width // 4
        fixed = markers(columns)
        n = 0
        for i in range(256):
            if i in fixed:
                value = fixed[i]
            else:
                value = values[n]; n += 1
            x, y = (i % columns) * 4, (i // columns) * 4
            image.paste(PALETTE[value], (x, y, x+4, y+4))
        image.save(folder / f'{name}.png')
        if name == 'fat':
            canvas = Image.new('RGB', (640, 480), (37, 45, 60))
            canvas.paste(image, (123, 207)); canvas.save(folder / 'fat-in-image.png')
    print(f'Generated three synthetic images in {folder}')

if __name__ == '__main__':
    main()
