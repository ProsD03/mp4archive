class MP4ArchiveFactory:
    def encode(self, *, input_path: str, output_path: str):
        raise NotImplementedError

    def decode(self, *, input_path: str, output_path: str):
        raise NotImplementedError

