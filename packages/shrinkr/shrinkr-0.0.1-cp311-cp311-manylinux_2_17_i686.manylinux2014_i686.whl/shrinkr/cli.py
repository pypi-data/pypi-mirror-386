import shrinkr
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py compress <algorithm> <file1> [file2 ...]")
        print("   or: python main.py decompress <compressed_file>")
        return 1

    mode = sys.argv[1]

    if mode == "compress":
        if len(sys.argv) < 4:
            print("Usage: python main.py compress <algorithm> <file1> [file2 ...]")
            print('Available algorithms: "rle"')
            return 1

        algorithm = sys.argv[2]
        files = sys.argv[3:]

        comp = shrinkr.CompressorFactory.create_by_name(algorithm)

        comp.compress(files)
        print(f"Compressed {len(files)} file(s) using {algorithm}")

    elif mode == "decompress":
        if len(sys.argv) < 3:
            print("Usage: python main.py decompress <compressed_file>")
            return 1

        compressed_file = sys.argv[2]

        with open(compressed_file, "rb") as f:
            first_byte = f.read(1)[0]

        comp = shrinkr.CompressorFactory.create_by_id(first_byte)

        comp.decompress([compressed_file])
        print(f"Decompressed {compressed_file}")

    else:
        print("Unknown mode: choose between compress|decompress")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
