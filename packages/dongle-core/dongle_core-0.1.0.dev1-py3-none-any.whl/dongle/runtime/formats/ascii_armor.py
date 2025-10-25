# SPDX-FileCopyrightText: 2025 led-inc.eu
# SPDX-FileContributor: Michael Meinel <led02@me.com>
#
# SPDX-License-Identifier: Apache-2.0

class ASCIIArmoredFile:
    BLOCK_START_MARKER = "-----BEGIN {}-----".format
    BLOCK_END_MARKER = "-----END {}-----".format

    @classmethod
    def make_block(cls, block_type, *block_data, **block_header):
        return [
            cls.BLOCK_START_MARKER(block_type),
            *(
                [*(f"{key}: {value}" for key, value in block_header.items()), ""]
                if block_header else []
            ),
            *block_data,
            cls.BLOCK_END_MARKER(block_type)
        ]

    @classmethod
    def load_headers(cls, block_data: [str]) -> (dict, [str]):
        index = 0
        headers = {}
        while index < len(block_data):
            if not block_data[index]:
                index += 1
                break

            elif ':' in block_data[index]:
                key, value = block_data[index].split(': ', 1)
                headers[key] = value
                index += 1

            else:
                break

        return headers, block_data[index:]

    @classmethod
    def load_block(
            cls,
            block_type: str,
            file_data: [str],
            *,
            start: int = 0,
            stop: int = -1) -> (dict, [str], (int, int)):

        if stop == -1:
            stop = len(file_data)

        block_start = file_data.index(cls.BLOCK_START_MARKER(block_type), start)
        block_end = file_data.index(cls.BLOCK_END_MARKER(block_type), block_start + 1, stop)

        headers, block_data = cls.load_headers(file_data[block_start + 1:block_end])
        return headers, block_data, (block_start, block_end)

__signature__ = "MGUCMGIZ26y1PMsSZ3Vmag/kP/8iWVeiG5jhKEw9CFIl4SgUVLhNZyaLi4nse0bU3aywLgIxALhrGWXKSoirhNeiA/O2OQ82OmGY1LCSPJdC5aQZV4Tju9SkpU4nqpBhqzbDKIjwWQ=="
