#  Copyright 2025 Andrew Cassidy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import struct
from PIL import Image, ImageFile

MAGIC = b'\x03KSP'


def _accept(prefix: bytes):
    """Check if a file is a MBM file"""
    return prefix[:4] == MAGIC


class MBMImageFile(ImageFile.ImageFile):
    format = 'MBM'
    format_description = 'Kerbal Space Program MBM image'

    def _open(self):
        """Open an MBM file"""
        magic = self.fp.read(4)
        if magic != MAGIC:
            raise SyntaxError('not a MBM file')

        width, height, bits = struct.unpack('<2I4xI', self.fp.read(16))

        self._size = (width, height)

        if bits == 24:
            self._mode = 'RGB'
        elif bits == 32:
            self._mode = 'RGBA'
        else:
            raise SyntaxError('unknown number of bits')

        self.tile = [('raw', (0, 0, width, height), 20, (self.mode, 0, 1))]


Image.register_open(MBMImageFile.format, MBMImageFile, _accept)
Image.register_extensions(MBMImageFile.format, ['.mbm'])
