from PIL import Image


class MP4ArchiveFactory:
    __size__ = 1080

    __divisions__ = 20
    __divisions_size__ = int(__size__ / __divisions__)

    __metadata_divisions__ = 5
    __metadata_divisions_size__ = int(__size__ / __metadata_divisions__)
    __metadata_header__ = "E7E02A"

    def __init__(self, size: int = None, divisions: int = None):
        if size:
            self.__size__ = size
        if divisions:
            self.__divisions__ = divisions

    def __create_metadata__(self) -> Image:
        image = Image.new('RGB', (self.__size__, self.__size__))
        pixels = []

        divisions_hex = hex(self.__divisions__)
        while len(divisions_hex) < 8:
            divisions_hex = divisions_hex + "0"
        divisions_hex = divisions_hex[2:-1]

        pixels.append((int(self.__metadata_header__[0:2], 16), int(self.__metadata_header__[2:4], 16),
                       int(self.__metadata_header__[4:6], 16)))
        pixels.append((int(divisions_hex[0:2], 16), int(divisions_hex[2:4], 16),
                       int(divisions_hex[4:6], 16)))

        print(pixels)

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
        self.__create_metadata__().save(".\\metadata.png") # DEBUG
        pixels = []
        images = []
        with open(input_file, "rb") as f:
            color_bytes = []
            data = f.read()
            for i in range(len(data) - 1, ):
                color_bytes.append(data[i:i + 2].hex())
                if len(color_bytes) == 3:
                    pixels.append((int(color_bytes[0], 16), int(color_bytes[1], 16), int(color_bytes[2], 16)))
                    color_bytes = []
        image = Image.new('RGB', (self.__size__, self.__size__))
        i = 0
        while len(pixels) > 0:
            for y_origin in range(self.__divisions__):
                for x_origin in range(self.__divisions__):
                    for y_offset in range(self.__divisions_size__):
                        for x_offset in range(self.__divisions_size__):
                            color = pixels[0] if len(pixels) != 0 else (0, 0, 0)
                            image.putpixel(((x_origin * self.__divisions_size__) + x_offset,
                                            (y_origin * self.__divisions_size__) + y_offset), color)
                    if len(pixels) != 0:
                        pixels.pop(0)
            images.append(image)
            image.save(f".\\out\\{i}.png") # DEBUG
            i = i + 1
