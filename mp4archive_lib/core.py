import os

from PIL import Image
import cv2
import numpy as np
from tqdm import tqdm

class MP4ArchiveFactory:
    __size__ = 1080

    __divisions__ = 20
    __divisions_size__ = int(__size__ / __divisions__)

    __metadata_divisions__ = 4
    __metadata_divisions_size__ = int(__size__ / __metadata_divisions__)
    __metadata_header__ = "E7E02A"

    def __init__(self, size: int = None, divisions: int = None):
        if size:
            self.__size__ = size
        if divisions:
            self.__divisions__ = divisions

    def __create_metadata__(self, filename: str) -> Image:
        image = Image.new('RGB', (self.__size__, self.__size__))
        pixels = []
        color_bytes = []

        pixels.append((int(self.__metadata_header__[0:2], 16), int(self.__metadata_header__[2:4], 16),
                       int(self.__metadata_header__[4:6], 16)))

        file = os.path.split(filename)[1]
        name, ext = os.path.splitext(file)
        name = filename.encode('utf-8').hex()
        ext = ext.encode('utf-8').hex()

        for i in range(10):
            if i > len(name) - 1:
                break
            color_bytes.append(name[i:i + 2])
            if len(color_bytes) == 3:
                pixels.append((int(color_bytes[0], 16), int(color_bytes[1], 16), int(color_bytes[2], 16)))
                color_bytes = []

        pixels.append((0, 0, 0))
        color_bytes = []

        for i in range(3):
            if i > len(ext) - 1:
                break
            color_bytes.append(ext[i:i + 2])
            if len(color_bytes) == 3:
                pixels.append((int(color_bytes[0], 16), int(color_bytes[1], 16), int(color_bytes[2], 16)))
                color_bytes = []

        divisions_hex = hex(self.__divisions__)
        while len(divisions_hex) < 8:
            divisions_hex = divisions_hex + "0"
        divisions_hex = divisions_hex[2:-1]

        pixels.append((int(divisions_hex[0:2], 16), int(divisions_hex[2:4], 16),
                       int(divisions_hex[4:6], 16)))

        while len(pixels) > 0:
            for y_origin in range(self.__metadata_divisions__):
                for x_origin in range(self.__metadata_divisions__):
                    for y_offset in range(self.__metadata_divisions_size__):
                        for x_offset in range(self.__metadata_divisions_size__):
                            color = pixels[0] if len(pixels) != 0 else (0, 0, 0)
                            image.putpixel(((x_origin * self.__metadata_divisions_size__) + x_offset,
                                            (y_origin * self.__metadata_divisions_size__) + y_offset), color)
                    if len(pixels) != 0:
                        pixels.pop(0)

        return image

    def encode(self, input_file: str, output_file: str):
        pixels = []
        images = [self.__create_metadata__(input_file)]
        with open(input_file, "rb") as f:
            color_bytes = []
            data = f.read()
            for i in range(len(data) - 1):
                color_bytes.append(data[i:i + 1].hex())
                if len(color_bytes) == 3:
                    pixels.append((int(color_bytes[0], 16), int(color_bytes[1], 16), int(color_bytes[2], 16)))
                    color_bytes = []

        pbar = tqdm(total=len(pixels))
        pbar.set_description("Converting File into Frames... ")
        while len(pixels) > 0:
            image = Image.new('RGB', (self.__size__, self.__size__))
            for y_origin in range(self.__divisions__):
                for x_origin in range(self.__divisions__):
                    for y_offset in range(self.__divisions_size__):
                        for x_offset in range(self.__divisions_size__):
                            color = pixels[0] if len(pixels) != 0 else (0, 0, 0)
                            image.putpixel(((x_origin * self.__divisions_size__) + x_offset,
                                            (y_origin * self.__divisions_size__) + y_offset), color)

                    if len(pixels) != 0:
                        pixels.pop(0)
                        pbar.update(1)
            images.append(image.copy())
        pbar.close()

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output_file, fourcc, 40, (self.__size__, self.__size__))
        pbar = tqdm(total=len(images))
        pbar.set_description("Encoding MP4... ")
        for img in images:
            video.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
            pbar.update(1)
        video.release()
        pbar.close()