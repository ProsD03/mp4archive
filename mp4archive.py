import argparse
import os
import sys
import warnings

from mp4archive_lib.core import MP4ArchiveFactory


class CustomParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


parser = CustomParser()
mainop = parser.add_mutually_exclusive_group()
mainop.add_argument('-e', '--encode', help="path to file to encode into video")
mainop.add_argument('-d', '--decode', help="path to video to decode into file")

parser.add_argument("-o", "--output", help="desired path for the output", required=True)

parser.add_argument("-n", "--nometadata",
                    help="in encode mode, disables metadata generation. in decode mode, enables heuristic checks", action="count",
                    default=0)
parser.add_argument("-d", "--divisions", help="number of divisions to divide the video into", type=int, default=15)
parser.add_argument("-s", "--size", help="size of square video in pixels (SxS)", type=int, default=1080)

args = parser.parse_args()

if args.encode:
    if not os.path.isfile(args.encode):
        sys.stderr.write(f"error: value of -e/--encode must be a valid file path (value: {args.encode})")
        exit(1)
    if args.output.split(".")[-1] != "mp4":
        warnings.warn(
            "output path should be an mp4 file. extension has been added for convenience, but program may crash if path is a directory.",
            RuntimeWarning)
        args.output += ".mp4"
    encoder = MP4ArchiveFactory(size=args.size, divisions=args.divisions)
    encoder.encode(input_path=args.encode, output_path=args.output, no_metadata=args.nometadata)

elif args.decode:
    if not os.path.isfile(args.decode):
        sys.stderr.write(f"error: value of -d/--decode must be a valid file path (value: {args.encode})")
        exit(1)
    if not os.path.isdir(args.output):
        sys.stderr.write(f"error: value of -o/--output must be a valid directory path (value: {args.encode})")
        exit(1)
    decoder = MP4ArchiveFactory()
    decoder.decode(input_path=args.decode, output_path=args.output, no_metadata=args.nometadata)
else:
    parser.print_help()
