import argparse
import hashlib
import lzma
import math
import os
import random
import tarfile
import tempfile

from PIL import Image

HEADER_SIZE = 5            # chunk_number (1 byte), total_chunks (1), size (3)
HASH_SIZE = 32             # SHA-256 digest size

def to_grayscale(v):
    return [0, 85, 170, 255][v]

def from_grayscale(g):
    if g < 43: return 0
    elif g < 128: return 1
    elif g < 213: return 2
    else: return 3

def bytes_to_2bit_pixels(data: bytes):
    pixels = []
    for byte in data:
        for shift in [6, 4, 2, 0]:
            pixels.append((byte >> shift) & 0b11)
    return pixels

def pixels_to_bytes(pixels):
    result = []
    for i in range(0, len(pixels), 4):
        chunk = pixels[i:i+4]
        while len(chunk) < 4:
            chunk.append(random.randint(0, 3))
        byte = (chunk[0] << 6) | (chunk[1] << 4) | (chunk[2] << 2) | chunk[3]
        result.append(byte)
    return bytes(result)

def is_valid_scale(width, height, scale):
    return math.gcd(width, height) % scale == 0

def xor_chain(data: bytes, password: str, iv: int = 0x42) -> bytes:
    key = hashlib.sha256(password.encode()).digest()
    prev = iv
    result = bytearray()
    for i, b in enumerate(data):
        k = key[i % len(key)]
        c = b ^ k ^ prev
        result.append(c)
        prev = c
    return bytes(result)

def xor_chain_decrypt(data: bytes, password: str, iv: int = 0x42) -> bytes:
    key = hashlib.sha256(password.encode()).digest()
    prev = iv
    result = bytearray()
    for i, b in enumerate(data):
        k = key[i % len(key)]
        p = b ^ k ^ prev
        result.append(p)
        prev = b
    return bytes(result)

def make_chunk_payload(raw_data: bytes, chunk_num: int, total_chunks: int, password: str, max_payload: int) -> bytes:
    size = len(raw_data)
    header = bytes([chunk_num, total_chunks]) + size.to_bytes(3, 'big')
    payload = header + raw_data
    digest = hashlib.sha256(payload).digest()
    final = payload + digest
    if len(final) > max_payload:
        raise ValueError("Chunk too large for image")
    final += os.urandom(max_payload - len(final))
    return xor_chain(final, password)

def parse_chunk_payload(image_path: str, encrypted: bytes, password: str):
    decrypted = xor_chain_decrypt(encrypted, password)
    if len(decrypted) < HEADER_SIZE + HASH_SIZE:
        raise ValueError("Decrypted chunk too small")
    chunk_num = decrypted[0]
    total = decrypted[1]
    size = int.from_bytes(decrypted[2:5], 'big')
    expected_end = HEADER_SIZE + size + HASH_SIZE
    segment = decrypted[:expected_end]
    data = segment[:-HASH_SIZE]
    expected_hash = segment[-HASH_SIZE:]
    if hashlib.sha256(data).digest() != expected_hash:
        raise ValueError(f"Chunk {image_path}: hash mismatch")
    return chunk_num, total, data[HEADER_SIZE:]

def encode_chunk_to_image(chunk_data, chunk_num, total_chunks, scale, width, height, password):
    if not is_valid_scale(width, height, scale):
        raise ValueError("Invalid scale for given resolution")
    img_w, img_h = width // scale, height // scale
    max_pixels = img_w * img_h
    max_bytes = (max_pixels * 2) // 8
    encrypted_payload = make_chunk_payload(chunk_data, chunk_num, total_chunks, password, max_bytes)
    pixels = bytes_to_2bit_pixels(encrypted_payload)
    gray = [to_grayscale(p) for p in pixels]
    img = Image.new('L', (img_w * scale, img_h * scale), 0)
    pix = img.load()
    for i, g in enumerate(gray):
        x, y = i % img_w, i // img_w
        for dy in range(scale):
            for dx in range(scale):
                pix[x * scale + dx, y * scale + dy] = g
    return img

def average_block(pixels, x, y, scale, width, height):
    total = 0
    count = 0
    for dy in range(scale):
        for dx in range(scale):
            px, py = x * scale + dx, y * scale + dy
            if 0 <= px < width and 0 <= py < height:
                total += pixels[px, py]
                count += 1
    return total // count if count else 0

def decode_image_to_chunk(image_path: str, scale: int, password: str):
    img = Image.open(image_path).convert('L')
    width, height = img.size
    cols, rows = width // scale, height // scale
    pixels = img.load()
    gray_values = []
    for y in range(rows):
        for x in range(cols):
            avg = average_block(pixels, x, y, scale, width, height)
            gray_values.append(from_grayscale(avg))
    raw_bytes = pixels_to_bytes(gray_values)
    return parse_chunk_payload(image_path, raw_bytes, password)

def compress_folder(folder_path: str) -> bytes:
    base = os.path.basename(folder_path.rstrip("/"))
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        with tarfile.open(fileobj=tmp, mode='w') as tar:
            tar.add(folder_path, arcname=base)
        tmp.flush()
        with open(tmp.name, "rb") as f:
            compressed = lzma.compress(f.read())
    os.remove(tmp.name)
    return compressed

def decompress_to_folder(data: bytes, output_dir: str):
    raw = lzma.decompress(data)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(raw)
        tmp.flush()
        with tarfile.open(tmp.name) as tar:
            tar.extractall(output_dir)
    os.remove(tmp.name)

def split_chunks(data, size):
    return [data[i:i+size] for i in range(0, len(data), size)]

def encode_folder(folder, width, height, output_dir, scale, password):
    os.makedirs(output_dir, exist_ok=True)
    compressed = compress_folder(folder)
    cols, rows = width // scale, height // scale
    max_bytes = (cols * rows * 2) // 8
    usable_bytes = max_bytes - HEADER_SIZE - HASH_SIZE
    chunks = split_chunks(compressed, usable_bytes)
    total = len(chunks)
    for idx, chunk in enumerate(chunks, 1):
        img = encode_chunk_to_image(chunk, idx, total, scale, width, height, password)
        fname = f"{os.path.basename(os.path.abspath(folder))}_{idx:03d}_of_{total:03d}.png"
        img.save(os.path.join(output_dir, fname))
        print(f"[+] Encoded chunk {idx}/{total}: {fname}")

def decode_folder(input_dir, output_dir, scale, password):
    files = sorted(f for f in os.listdir(input_dir) if f.lower().endswith('.png'))
    chunks = {}
    total = None
    for f in files:
        path = os.path.join(input_dir, f)
        idx, t, chunk = decode_image_to_chunk(path, scale, password)
        if total is None:
            total = t
        chunks[idx] = chunk
        print(f"[+] Decoded chunk {idx}/{total}")
    if len(chunks) != total:
        raise ValueError("Missing chunks during decoding")
    combined = b''.join(chunks[i] for i in range(1, total + 1))
    decompress_to_folder(combined, output_dir)
    print(f"[✓] Folder successfully reconstructed at: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Encode/decode a folder into grayscale image chunks.")
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="Compress and encode a folder into images")
    enc.add_argument("folder", help="Folder to encode")
    enc.add_argument("--width", type=int, default=1920)
    enc.add_argument("--height", type=int, default=1080)
    enc.add_argument("--scale", type=int, default=4)
    enc.add_argument("--outdir", default="image_chunks")
    enc.add_argument("--password", required=True)

    dec = sub.add_parser("decode", help="Decode images back into original folder")
    dec.add_argument("inputdir", help="Directory containing chunked images")
    dec.add_argument("outputdir", help="Where to extract the reconstructed folder")
    dec.add_argument("--scale", type=int, default=4)
    dec.add_argument("--password", required=True)

    args = parser.parse_args()
    if args.command == "encode":
        encode_folder(args.folder, args.width, args.height, args.outdir, args.scale, args.password)
    elif args.command == "decode":
        decode_folder(args.inputdir, args.outputdir, args.scale, args.password)

if __name__ == "__main__":
    main()
