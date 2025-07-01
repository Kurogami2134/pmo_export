"""
struct Header {
    filesize uint,
    flags uint[3], # may be the ones used in gimconv
    dataSize uint,
    dataFlags uint,
    dataType uint,
    width ushort,
    height ushort
}

struct Palette {
    size uint,
    flags uint,
    type uint,
    count uint,
    paletteData byte[count*color_size]
}

struct GIM {
    header Header,
    imageData byte[header.width*header.height*index_size],
    palette Palette
}
"""
import bpy
try:
    from PIL import Image
except:
    from subprocess import check_output
    import sys

    check_output([sys.executable, '-m', 'pip', 'install', 'pillow', f'--target={bpy.utils.user_resource("SCRIPTS", path="modules")}'])
    from PIL import Image

import numpy as np
from struct import pack
from enum import Enum
from typing import BinaryIO
from io import BytesIO

INDEX_FORMAT = [
    (4, 4),  # CLUT4
    (5, 8),  # CLUT8
]

WIDTH_BLOCK = 16
HEIGHT_BLOCK = 8

class ColorLimitError(Exception):
    def __init__(self, msg="Color count over 256"):
        self.msg = msg
        super().__init__(self.msg)

class PaletteType(Enum):
    RGBA5650 = 0
    RGBA5551 = 1
    RGBA4444 = 2
    RGBA8888 = 3


class GimImage:
    def __init__(self) -> None:
        self.flags = [0, 1, 1]
        self.height, self.width = 0, 0
        self.palette: Palette = Palette()
        self.pixels: list[int] = []
        self.data_flag: int = 1
    
    @property
    def data_type(self) -> int:
        for index, pow in INDEX_FORMAT:
            if max(self.pixels) < 2**pow:
                return index
        return -1
    
    @property
    def size(self) -> int:
        return self.data_size + self.palette.size + 0x10
    
    @property
    def data_size(self) -> int:
        return int(self.width*self.height / (2 if self.data_type == 4 and self.width >= 32 else 1)) + 0x10
    
    @property
    def img_data(self) -> bytes:
        match self.data_type:
            case 4:
                modifier = 2
            case 5:
                modifier = 1
            case _:
                raise ColorLimitError
        
        data = []
        
        L_WIDTH_BLOCK = min(WIDTH_BLOCK*modifier, self.width)
        for block_v in range(max(1, self.height // HEIGHT_BLOCK)):
            for block_h in range(max(1, self.width // L_WIDTH_BLOCK)):
                for pixel_v in range(HEIGHT_BLOCK):
                    for pixel_h in range(L_WIDTH_BLOCK):
                        offset = (block_v*HEIGHT_BLOCK+pixel_v) * self.width + (block_h*L_WIDTH_BLOCK+pixel_h)
                        data.append(self.pixels[offset])

        if self.data_type == 4:
            data = [x | y << 4 for x, y in zip(data[::2], data[1::2])]
            if self.width < 32:
                data = self.add_padding_blocks(data)
        else:
            data = data
        
        data = b''.join(map(lambda x: pack("B", x), data))
        
        print(f'Expected image data size: {len(data)}\nImage data size: {self.data_size-16}')
        
        return data
    
    def write(self, file) -> None:
        self.palette.add_padding(self.data_type)
        file.write(pack("4i", self.size, *self.flags))
        
        file.write(pack("3i", self.data_size, self.data_flag, self.data_type))
        file.write(pack("2H", self.width, self.height))
        file.write(self.img_data)
        self.palette.write(file)

    def add_padding_blocks(self, pixels) -> None:
        img = []
        res = []
        for y in range(self.height):
            img.append([pixels.pop(0) for x in range(self.width//2)] + [0]*8)
        for row in img:
            res.extend(row)
        return res


class TMH:
    def __init__(self) -> None:
        self.images: GimImage = []

    @property
    def img_count(self) -> int:
        return len(self.images)

    def buildTMH(self, fd) -> None:
        fd.write(b'.TMH0.14')
        fd.write(pack("I4x", self.img_count))
        
        for img in self.images:
            img.write(fd)
    
    def loadImg(self, node) -> None:
        self.images.append(nodeToImage(node))


class Palette:
    def __init__(self, color_priority: bool = False) -> None:
        self.flags: int = 2
        self.colors: list[tuple[float, float, float, float]] = []
        self.color_priority: int = color_priority

    def add_padding(self, index_type: int):
        match index_type:
            case 4:
                self.colors.extend([(0.0, 0.0, 0.0, 1.0)]*(16-self.count))
            case 5:
                self.colors.extend([(0.0, 0.0, 0.0, 1.0)]*(256-self.count))

    @property
    def type(self) -> int:
        alpha = set(map(lambda x: x[3], self.colors))
        color = len(set(map(lambda x: x[3], self.colors)))
        if alpha == {1.0}:
            return PaletteType.RGBA5650
        
        if alpha == {0.0, 1.0} and not self.color_priority:
            return PaletteType.RGBA5551

        if color > 2**4:
            return PaletteType.RGBA8888

        return PaletteType.RGBA4444

    @property
    def color_size(self) -> int:
        return 4 if self.type == PaletteType.RGBA8888 else 2

    @property
    def count(self) -> int:
        return len(self.colors)

    @property
    def size(self) -> int:
        return (16 if self.count <= 16 else 256) * self.color_size + 0x10

    @property
    def bin_colors(self) -> bytes:
        match self.type:
            case PaletteType.RGBA5650:
                func = lambda x: (int(x[0]*(2**5-1)) | int(x[1]*(2**6-1)) << 5 | int(x[2]*(2**5-1)) << 11)
            case PaletteType.RGBA5551:
                func = lambda x: (int(x[0]*(2**5-1)) | int(x[1]*(2**5-1)) << 5 | int(x[2]*(2**5-1)) << 10 | int(x[3]) << 15)
            case PaletteType.RGBA4444:
                func = lambda x: (int(x[0]*(2**4-1)) | int(x[1]*(2**4-1)) << 4 | int(x[2]*(2**4-1)) << 8 | int(x[3]*(2**4-1)) << 12)
            case PaletteType.RGBA8888:
                func = lambda x: (int(x[0]*(2**8-1)) | int(x[1]*(2**8-1)) << 8 | int(x[2]*(2**8-1)) << 16 | int(x[3]*(2**8-1)) << 24)

        for color in self.colors:
            yield func(color)


    def write(self, fd) -> None:
        fd.write(pack("4I", self.size, self.flags, self.type.value, self.count))
        fd.write(pack(f'<{self.count}{"I" if self.color_size == 4 else "H"}', *self.bin_colors))


def nodeToImage(node) -> GimImage:
    img = list(node.image.pixels)
    img = list(zip(img[::4], img[1::4], img[2::4], img[3::4]))
    width, height = node.image.size
    array = []
    for row in range(height):
        row = []
        array.append(row)
        for column in range(width):
            row.append(img.pop(0))
    
    pixels = list(reversed(array))

    colors = []
    indices = []
    for row in pixels:
        for column in row:
            if tuple(column) not in colors:
                colors.append(tuple(column))
            indices.append(colors.index(tuple(column)))

    colors = list(map(lambda y: list(map(lambda x: x, y)), colors))
    
    gim = GimImage()
    pal = gim.palette

    gim.width, gim.height = width, height
    gim.pixels = indices
    pal.colors = colors
    return gim


class PAC:
    def __init__(self) -> None:
        self.files: list[BinaryIO] = []
    
    def save(self, path: str):
        with open(path, "wb") as file:
            file_start: int = 4 + 8 * len(self.files)
            file_start += 16 - (file_start % 16)
            file_data: list[tuple[int, int]] = []

            file.write(pack("I", len(self.files)))
            file.seek(file_start)

            for entry in self.files:
                file.seek(file.tell() + 16 - (file.tell() % 16))
                entry.seek(0)
                data = entry.read()
                file_data.append((file.tell(), len(data)))
                file.write(data)
            
            file.seek(4)
            for offset, length in file_data:
                file.write(pack("2I", offset, length))

    def add(self) -> BinaryIO:
        file = BytesIO()
        self.files.append(file)
        return file
