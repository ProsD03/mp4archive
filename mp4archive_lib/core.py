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
    def _metadata_frame(self):
        frame = np.array([[[0, 0, 0] for i in range(3)] for i in range(3)])
        frame[0, 0] = self._hex_to_rgb(self._magic)
        frame[0, 1] = (self._divisions, 0, 0)

        hex_extension = self._extension.encode("ascii").hex()
        while len(hex_extension) < 6:
            hex_extension += 0
        frame[0, 2] = self._hex_to_rgb(hex_extension)
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

    def _decode_metadata(self, *, frame: np.array):
        if frame.shape != (3, 3, 3):
            raise ValueError("Metadata must be a RGB frame of 3x3 pixels.")
        if not np.array_equal(frame[0, 0], self._hex_to_rgb(self._magic)):
            raise ValueError("Video is not compatible or was not made with MP4Archive_lib.")
        self._divisions = frame[0, 1, 0]
        self._extension = ''.join([chr(frame[0, 2, n]) for n in range(3)])

        pos = 0
        temp_name = ""
        while pos != 6:
            pixel = frame[1 + pos // 3, pos % 3]
            for byte in pixel:
                if byte != 0:
                    temp_name += chr(byte)
            pos += 1
        self._filename = temp_name

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
                                             '-crf': '0',
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
        reader = skvideo.io.FFmpegReader(input_path)
        self._size = reader.getShape()[1]
        metadata = None
        writer = None
        progress = tqdm.tqdm(total=(reader.getShape()[0] - 1) * (self._divisions * self._divisions) * 3,
                             desc="Decoding...", unit="bytes")
        for frame in reader:
            if metadata is None:
                frame = frame[::self._size // 3, ::self._size // 3]
                metadata = frame
                self._decode_metadata(frame=metadata)
                writer = open(f"{output_path}{os.sep}{self._filename}.{self._extension}", "wb")
            else:
                pos = 0
                frame = frame[::self._size // self._divisions, ::self._size // self._divisions]
                while pos // self._divisions < self._divisions:
                    pixel = frame[pos // self._divisions, pos % self._divisions]
                    for byte in pixel:
                        writer.write(byte)
                        progress.update(1)
                    pos += 1
        writer.close()
        reader.close()
