import skvideo.io
import numpy as np
import tqdm
import string
import os

np.int = np.int32
np.float = np.float64
np.bool = np.bool_


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
                frame[1 + pos // 3, pos % 3] = codepoints
                pos += 1
                codepoints.clear()
        return frame.repeat(self._size // 3, axis=0).repeat(self._size // 3, axis=1)

    def __init__(self, *args, **kwargs):
        assert skvideo.getFFmpegPath()
        self._size = kwargs.get('size', self._size)
        self._divisions = kwargs.get('divisions', self._divisions)

    def encode(self, *, input_path: str, output_path: str):
        filename, ext = os.path.splitext(os.path.basename(input_path))
        self._filename = filename
        self._extension = ext.split(".")[-1]

        with open(input_path, "rb") as f:
            data = f.read()

        writer = skvideo.io.FFmpegWriter(output_path,
                                         outputdict={
                                             '-vcodec': 'libx264rgb',
                                             '-pix_fmt': 'rgb24',
                                             '-colorspace': 'rgb',
                                         })
        writer.writeFrame(self._metadata_frame)

        tempbytes = []
        frame = np.array([[[0, 0, 0] for i in range(self._divisions)] for i in range(self._divisions)])
        pos = 0

        progress = tqdm.tqdm(total=len(data), desc="Encoding...", unit="bytes")
        for i, byte in enumerate(data):
            tempbytes.append(byte)
            progress.update(1)
            if i == len(data) - 1 and len(tempbytes) < 3:
                while len(tempbytes) < 3:
                    tempbytes.append(0)
            if len(tempbytes) == 3:
                frame[pos // self._divisions, pos % self._divisions] = tempbytes
                pos += 1
                tempbytes.clear()
            if pos // self._divisions >= self._divisions:
                writer.writeFrame(
                    frame.repeat(self._size // self._divisions, axis=0).repeat(self._size // self._divisions, axis=1))
                pos = 0
                frame = np.array([[[0, 0, 0] for i in range(self._divisions)] for i in range(self._divisions)])

        writer.close()

        def decode(self, *, input_path: str, output_path: str):
            # smaller_img = bigger_img[::2, ::2]
            raise NotImplementedError
