import skvideo
import numpy as np
import string


class MP4ArchiveFactory:
    _magic = "454C45"

    _size = 1080
    _divisions = 15

    _extension = "bin"
    _filename = "filename"

    @staticmethod
    def _hex_to_rgb(hexcode: str):
        if len(hexcode) != 6:
            raise ValueError(f"Hexcode {hexcode} must be 6 digits (3 bytes).")
        elif not all(c in string.hexdigits for c in hexcode):
            raise ValueError(f"Hexcode {hexcode} must a valid hex number.")
        return int(hexcode[:2], 16), int(hexcode[2:4], 16), int(hexcode[4:], 16)

    @property
    def _division_size(self):
        return self._size // self._divisions

    @property
    def _metadata_frame(self):
        frame = np.array([[[0, 0, 0] for i in range(3)] for i in range(3)])
        frame[0, 0] = self._hex_to_rgb(self._magic)
        frame[0, 1] = (self._divisions, 0, 0)
        frame[0, 2] = self._hex_to_rgb(self._extension.encode("ascii").hex())

        codepoints = []
        pos = 0
        for i, char in enumerate(self._filename):
            if pos == 6:
                break
            codepoints.append(ord(char))
            if i == len(self._filename) - 1 and len(codepoints) < 3:
                while len(codepoints) < 3:
                    codepoints.append(0)
            if len(codepoints) == 3:
                frame[1 + pos//3, pos % 3] = codepoints
                pos += 1
                codepoints.clear()
        return frame

    def __init__(self, *args, **kwargs):
        assert skvideo.getFFmpegPath()
        self._size = kwargs.get('size', self._size)
        self._divisions = kwargs.get('divisions', self._divisions)
        print(self._metadata_frame)

    def encode(self, *, input_path: str, output_path: str):
        raise NotImplementedError

    def decode(self, *, input_path: str, output_path: str):
        raise NotImplementedError
