#!/usr/bin/env python3
"""
A tool for splitting files in multiple parts and joining them at a later time.
"""

import argparse
import hashlib
import math
import os
import sys
from pathlib import Path


_SUFFIX_PREFIX = '.hacha'


class HachaError(Exception):
    pass


def split(src_filepath: Path, max_part_size: int, dst_dirpath: Path) -> list[Path]:
    result = []

    dst_template_filename = f'{src_filepath.name}{_SUFFIX_PREFIX}'

    with open(src_filepath, 'rb') as f:
        file_size = f.seek(0, os.SEEK_END)
        f.seek(0)

        part_count = math.ceil(file_size / max_part_size)
        part_digits = len(str(part_count))

        bytes_to_read = file_size

        for i in range(part_count):
            dst_filepath = dst_dirpath / f'{dst_template_filename}{i:0{part_digits}}'

            part_size = min(max_part_size, bytes_to_read)
            dst_filepath.write_bytes(f.read(part_size))
            bytes_to_read -= part_size

            result.append(dst_filepath)

    return result


def join(src_filepath: Path, dst_path: Path) -> Path:
    dst_filename = src_filepath.name.rsplit(_SUFFIX_PREFIX, maxsplit=1)[0]

    if dst_path.name == dst_filename:
        dst_dirpath = dst_path.parent
        dst_filepath = dst_path
    elif dst_path.is_dir():
        dst_dirpath = dst_path
        dst_filepath = dst_dirpath / dst_filename
    else:
        msg = (
            f'Destination path "{dst_path}" is neither a valid directory nor a filepath whose '
            f'name matches the basename of the source filepath (i.e. "{dst_filename}").'
        )
        raise HachaError(msg)

    src_part_filepaths = sorted(src_filepath.parent.glob(f'{dst_filename}{_SUFFIX_PREFIX}*'))
    if not src_part_filepaths:
        msg = f'Source filepath "{src_filepath}" does not appear to reference a valid part file.'
        raise HachaError(msg)

    with open(dst_filepath, 'wb') as f:
        for src_part_filepath in src_part_filepaths:
            f.write(src_part_filepath.read_bytes())

    return dst_filepath


def _create_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='hacha', description=__doc__)

    subparsers = parser.add_subparsers(help='Action to perform.', dest='command', required=True)

    split_parser = subparsers.add_parser('split', help='Split a file into multiple parts.')
    split_parser.add_argument(
        'input_file',
        type=Path,
        help='Path to the file that will be split.',
    )

    def binary_size(size: str) -> int:
        size = size.strip()

        for units, multiplier in (
            ('GiB', 1024**3),
            ('MiB', 1024**2),
            ('KiB', 1024**1),
            ('B', 1024**0),
        ):
            print(units)
            if size.endswith(units):
                try:
                    return int(size.removesuffix(units).strip()) * multiplier
                except ValueError as e:
                    msg = f'Unable to parse size "{size}" as integer'
                    raise argparse.ArgumentTypeError(msg) from e

        raise argparse.ArgumentTypeError(
            f'Unrecognized units in "{size}"; valid units are B, KiB, MiB, and GiB.',
        )

    split_parser.add_argument(
        'size',
        type=binary_size,
        help=(
            'Size for each of the part files. Valid units are B, KiB, MiB, and GiB. The last part '
            'file may be smaller than the given size.'
        ),
    )
    split_parser.add_argument(
        'output_directory',
        type=Path,
        help=(
            'Path to the directory where the part files will be written. The name of the output '
            'files starts with the basename of the input file with an added suffix that includes '
            'the part index.'
        ),
    )

    join_parser = subparsers.add_parser('join', help='Join part files into the original file.')
    join_parser.add_argument(
        'input_file',
        type=Path,
        help=(
            'Path to a part file (typically the part file with index 0, but any would work) that '
            'will be used to locate all the part files that need to be joined.'
        ),
    )
    join_parser.add_argument(
        'output_path',
        type=Path,
        help=(
            'Path to either the directory where the joined file will be written or a new file '
            'whose basename should match the original name of the previously split file.'
        ),
    )

    return parser


def _md5sum(filepath: Path) -> str:
    return hashlib.md5(filepath.read_bytes()).hexdigest()


def main() -> int:
    args = _create_args_parser().parse_args()

    try:
        if args.command == 'split':
            part_filepaths = split(args.input_file, args.size, args.output_directory)
            print(f'Input file MD5 checksum: {_md5sum(args.input_file)}')
            print('Output files:\n', '\n'.join(f'- "{p}"' for p in part_filepaths))
        else:
            joined_filepath = join(args.input_file, args.output_path)
            print(f'Output file: "{joined_filepath}"')
            print(f'Output file MD5 checksum: {_md5sum(joined_filepath)}')

    except HachaError as e:
        print(f'ERROR: {e}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
