import os
import threading

import skvideo.io
import numpy as np
from tqdm import tqdm


class AmbiguityError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class MP4ArchiveFactory:
    __hex_charset__ = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F"]

    __size__ = 1080

    __divisions__ = 20
    __divisions_size__ = int(__size__ / __divisions__)

    __metadata_divisions__ = 4
    __metadata_divisions_size__ = int(__size__ / __metadata_divisions__)
    __metadata_header__ = "E070E00020A0"

    def __init__(self, size: int = None, divisions: int = None):
        if size:
            self.__size__ = size
        if divisions:
            self.__divisions__ = divisions

    def __correct_byte__(self, byte: str) -> str:
        if len(byte) != 2:
            raise ValueError("Incorrect byte length. Byte must be 2 characters long.")
        nibbles = list(byte)
        print(nibbles)
        if nibbles[0] not in self.__hex_charset__ or nibbles[1] not in self.__hex_charset__:
            raise ValueError("Incorrect byte format. Byte must be hex.")

        if nibbles[1] == "0":
            return nibbles[0]

        tolerance_index = self.__hex_charset__.index(nibbles[1])
        data_index = self.__hex_charset__.index(nibbles[0])
        if tolerance_index == 8:
            raise AmbiguityError(
                "Byte is ambiguous, tolerance value is in the middle of the charset. Re-encode video with different settings.")
        elif tolerance_index > 8:
            if data_index == len(self.__hex_charset__) - 1:
                raise AmbiguityError(
                    "Byte is ambiguous, data value is already F but tolerance value indicates that the value must be rounded up. Re-encode video with different settings.")
            return self.__hex_charset__[data_index + 1]
        else:
            if data_index == 0:
                raise AmbiguityError(
                    "Byte is ambiguous, data value is already 0 but tolerance value indicates that the value must be rounded down. Re-encode video with different settings.")
            return self.__hex_charset__[data_index - 1]

    def __create_metadata__(self, filename: str) -> np.array:
        pixels = []
        color_bytes = []

        pixels.append((int(self.__metadata_header__[0:2], 16), int(self.__metadata_header__[2:4], 16),
                       int(self.__metadata_header__[4:6], 16)))
        pixels.append((int(self.__metadata_header__[6:8], 16), int(self.__metadata_header__[8:10], 16),
                       int(self.__metadata_header__[10:12], 16)))

        file = os.path.split(filename)[1]
        name, ext = os.path.splitext(file)
        name = filename.encode('utf-8').hex()
        ext = ext.encode('utf-8').hex()

        for i in range(20):
            if i > len(name) - 1:
                break
            color_bytes.append(name[i] + "0")
            if len(color_bytes) == 3:
                pixels.append((int(color_bytes[0], 16), int(color_bytes[1], 16), int(color_bytes[2], 16)))
                color_bytes = []

        pixels.append((0, 0, 0))
        color_bytes = []

        for i in range(6):
            if i > len(ext) - 1:
                break
            color_bytes.append(ext[i] + "0")
            if len(color_bytes) == 3:
                pixels.append((int(color_bytes[0], 16), int(color_bytes[1], 16), int(color_bytes[2], 16)))
                color_bytes = []

        pixels.append((0, 0, 0))

        divisions_hex = hex(self.__divisions__)
        while len(divisions_hex) <= 8:
            divisions_hex = divisions_hex + "0"
        divisions_hex = divisions_hex[2:-1]

        for i in range(len(divisions_hex)):
            color_bytes.append(divisions_hex[i] + "0")
            if len(color_bytes) == 3:
                pixels.append((int(color_bytes[0], 16), int(color_bytes[1], 16), int(color_bytes[2], 16)))
                color_bytes = []

        frame = [[(0, 0, 0) for i in range(self.__size__)] for i in range(self.__size__)]

        while len(pixels) > 0:
            for y_origin in range(self.__metadata_divisions__):
                for x_origin in range(self.__metadata_divisions__):
                    if len(pixels) == 0:
                        break
                    color = pixels.pop(0)
                    for y_offset in range(self.__metadata_divisions_size__):
                        for x_offset in range(self.__metadata_divisions_size__):
                            frame[(y_origin * self.__metadata_divisions_size__) + y_offset][
                                (x_origin * self.__metadata_divisions_size__) + x_offset] = color
        return np.array(frame, dtype=np.uint8)

    def encode(self, input_file: str, output_file: str):
        pixels = []
        writer = skvideo.io.FFmpegWriter(output_file, outputdict={
            '-vcodec': 'libx264rgb',
            '-pix_fmt': 'rgb24',
            '-colorspace': 'rgb',
            '-preset': 'fast'
        })
        writer.writeFrame(self.__create_metadata__(input_file))
        with open(input_file, "rb") as f:
            data = f.read()
        color_bytes = []
        for i in range(len(data)):
            byte = hex(data[i]).split('x')[1]
            if len(byte) < 2:
                byte = byte + "0"
            for nibble in byte:
                color_bytes.append(nibble + "0")
                if len(color_bytes) == 3:
                    pixels.append((int(color_bytes[0], 16), int(color_bytes[1], 16), int(color_bytes[2], 16)))
                    color_bytes = []

        pbar = tqdm(total=len(pixels))
        pbar.set_description("Encoding... ")
        threads = []
        while len(pixels) > 0:
            frame = [[(0, 0, 0) for i in range(self.__size__)] for i in range(self.__size__)]
            for y_origin in range(self.__divisions__):
                for x_origin in range(self.__divisions__):
                    if len(pixels) == 0:
                        break
                    color = pixels.pop(0)
                    pbar.update(1)
                    for y_offset in range(self.__divisions_size__):
                        for x_offset in range(self.__divisions_size__):
                            frame[(y_origin * self.__divisions_size__) + y_offset][
                                (x_origin * self.__divisions_size__) + x_offset] = color
            threads.append(threading.Thread(target=writer.writeFrame, args=(np.array(frame, dtype=np.uint8),)))
            threads[-1].start()

        pbar.close()

        for thread in threads:
            thread.join()
        writer.close()

    def decode(self, input_file: str):
        return