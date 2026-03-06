import os


def read_last_lines(filename, n=500):
    try:
        with open(filename, "rb") as f:
            f.seek(0, os.SEEK_END)
            end = f.tell()
            buffer = bytearray()
            pointer = end
            while pointer >= 0 and len(buffer.split(b"\n")) <= n:
                pointer -= 1024
                f.seek(max(pointer, 0))
                new_data = f.read(min(1024, end - pointer))
                buffer = new_data + buffer
                if pointer < 0:
                    break

            lines = buffer.split(b"\n")
            for line in lines[-n:]:
                try:
                    decoded = line.decode("utf-8")
                    if (
                        "ERROR" in decoded
                        or "Traceback" in decoded
                        or "Exception" in decoded
                        or decoded.strip().startswith("File ")
                    ):
                        print(decoded)
                except:
                    pass
    except Exception as e:
        print(f"Error reading file: {e}")


if __name__ == "__main__":
    read_last_lines("logs/tir_yakit.log", 500)
