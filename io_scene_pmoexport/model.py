import struct

FU_MODEL = b'1.0\x00'
P3RD_MODEL = b'102\x00'


class PMODATA:
    def __init__(self) -> None:
        self.address: None | int = None
        self.size: int = 0

    def tobytes(self) -> bytes:
        pass

    def calcsize(self) -> int:
        return self.size

    def move(self, add) -> None:
        self.address = add

    def write(self, file) -> None:
        # add = file.tell()
        file.seek(self.address)
        file.write(self.tobytes())
        # file.seek(add)
    
    def __str__(self) -> str:
        return "\n".join([f'{k}: {v}' for k, v in self.__dict__.items()])


class PMOHeader(PMODATA):
    def __init__(self) -> None:
        super().__init__()
        self.size: int = 0x40
        self.pmo: bytes = b'pmo\x00'
        self.ver: bytes = b'102\x00'
        self.filesize: int = 0
        self.clippingDistance: float = 0
        self.scale: dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.meshCount: int = 0
        self.materialCount: int = 0
        self.meshHeaderOffset: int = 0x40
        self.tristripHeaderOffset: int = 0
        self.materialRemapOffset: int = 0
        self.boneDataOffset: int = 0
        self.materialDataOffset: int = 0
        self.meshDataOffset: int = 0

    def __repr__(self) -> str:
        return (f'Version: {"1.2(P3RD)" if self.ver == P3RD_MODEL else "1.0(FU)"}\n'
                f'Offsets:\n'
                f'\tMeshHeader:\t{hex(self.meshHeaderOffset)}\n'
                f'\tTriHeader:\t{hex(self.tristripHeaderOffset)}\n'
                f'\tMatRemap:\t{hex(self.materialRemapOffset)}\n'
                f'\tBoneData:\t{hex(self.boneDataOffset)}\n'
                f'\tMaterial:\t{hex(self.materialDataOffset)}\n'
                f'\tMeshData:\t{hex(self.meshDataOffset)}')

    def tobytes(self) -> bytes:
        byted = self.pmo + self.ver + struct.pack("I", self.filesize) + struct.pack("f", self.clippingDistance)
        byted += struct.pack("3f", *self.scale.values())
        byted += struct.pack("H", self.meshCount) + struct.pack("H", self.materialCount) + struct.pack(
            "I", self.meshHeaderOffset)
        byted += struct.pack("I", self.tristripHeaderOffset) + struct.pack("I", self.materialRemapOffset) + struct.pack(
            "I", self.boneDataOffset)
        byted += struct.pack("I", self.materialDataOffset) + struct.pack("I", self.meshDataOffset)
        byted += bytes(8)
        return byted


class MeshHeader(PMODATA):
    def __init__(self) -> None:
        super().__init__()
        self.size: int = 0x30
        self.scale: dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.unknown: bytes = (b'\x00\x00\x00\x00\x00\x00\x80?\x00\x00\x80?\x00\x00\x00\x00\x00\x00\x00\x00\x03'
                               b'\x00\x00\x802\x00\x00\xdf')
        self.materialCount: int = 0
        self.cumulativeMaterialCount: int = 0
        self.tristripCount: int = 0
        self.cumulativeTristripCount: int = 0

        self.meshes: list[Mesh] = []
        self.materials: list[Material] = []

    def update(self) -> None:
        self.materialCount = len(self.materials)
        self.tristripCount = len(self.meshes)

    def set_scale(self, scale) -> None:
        self.scale = scale

    def tobytes(self) -> bytes:
        byted = struct.pack("3f", *self.scale.values()) + self.unknown
        byted += struct.pack("H", self.materialCount) + struct.pack("H", self.cumulativeMaterialCount)
        byted += struct.pack("H", self.tristripCount) + struct.pack("H", self.cumulativeTristripCount)
        return byted


class FUMeshHeader(PMODATA):
    def __init__(self) -> None:
        super().__init__()
        self.size: int = 0x18
        self.uvscale: dict[str, float] = {"u": 1.0, "v": 1.0}
        self.unknown: bytes = b'\x03\x00\x00\x80\x00\x00\x00\x00'
        self.materialCount: int = 0
        self.cumulativeMaterialCount: int = 0
        self.tristripCount: int = 0
        self.cumulativeTristripCount: int = 0

        self.meshes: list[Mesh] = []
        self.materials: list[Material] = []

    def set_scale(self, scale) -> None:
        pass

    def update(self) -> None:
        self.materialCount = len(self.materials)
        self.tristripCount = len(self.meshes)

    def tobytes(self) -> bytes:
        byted = struct.pack("2f", *self.uvscale.values()) + self.unknown
        byted += struct.pack("H", self.materialCount) + struct.pack("H", self.cumulativeMaterialCount)
        byted += struct.pack("H", self.tristripCount) + struct.pack("H", self.cumulativeTristripCount)
        return byted


class TristripHeader(PMODATA):
    def __init__(self) -> None:
        super().__init__()
        self.size: int = 0x10
        self.materialOffset: int = 0
        self.weightCount: int = 0
        self.cumulativeWeightCount: int = 0
        self.meshOffset: int = 0
        self.vertexOffset: int = 0
        self.indexOffset: int = 0
        self.bones: list[int] = []

        self.backface_culling: bool = False
        self.alpha_blend: bool = False

    @property
    def bone_data(self) -> bytes:
        data = b''
        for bone in range(len(self.bones)):
            data += struct.pack("2b", bone, self.bones[bone])
            print(bone, self.bones[bone])

        return data

    def tobytes(self) -> bytes:
        return struct.pack("BbH3I", self.materialOffset, self.weightCount, self.cumulativeWeightCount, self.meshOffset,
                           self.vertexOffset, self.indexOffset)

    def __str__(self) -> str:
        return f'Tristrip header at: {self.address}\n' \
               f'Bone count {self.weightCount}/{self.cumulativeWeightCount+self.weightCount}\n' \
               f'Material: {self.materialOffset}'


class Material(PMODATA):
    def __init__(self) -> None:
        super().__init__()
        self.size: int = 0x10
        self.rgba: dict[str, int] = {"r": 0, "g": 0, "b": 0, "a": 0}
        self.rgba2: dict[str, int] = {"r": 0, "g": 0, "b": 0, "a": 0}
        self.textureIndex: int = 0
        self.unknown: bytes = b'\x00\x00\x00\x00'

    def tobytes(self) -> bytes:
        byted = b''
        for x in self.rgba.values():
            byted += struct.pack("B", int(x))
        for x in self.rgba2.values():
            byted += struct.pack("B", int(x))
        byted += struct.pack("i", self.textureIndex)
        byted += self.unknown
        return byted

    def __eq__(self, other) -> bool:
        return self.address == other.address


class Vertex(PMODATA):
    def __init__(self) -> None:
        super().__init__()
        self.postrans: int | None = None
        self.textrans: int | None = None
        self.nortrans: int | None = None
        self.weitrans: int | None = None
        self.color_trans: int | None = None
        self.scale: dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.verfor: str = "1B2H3b3h"  # vertex format
        self.size: int = self.calcsize()

        # vertex coordinates
        self.x: float = 0
        self.y: float = 0
        self.z: float = 0
        # uv coordinates
        self.u: float = 0
        self.v: float = 0
        # normals
        self.k: float = 0
        self.j: float = 0
        self.i: float = 0
        # weight
        self.w: None | list[int] = None
        self.color = None

    def calcsize(self) -> int:
        return struct.calcsize(self.verfor)

    def vt(self, u, v) -> None:
        self.u = float(u)
        self.v = float(v)

    def vn(self, i, j, k) -> None:
        self.k = float(k)
        self.j = float(j)
        self.i = float(i)

    def coords(self, x, y, z) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def to_pmo(self) -> bytes:
        data = []
        if self.weitrans is not None:
            data.extend([round(float(w)*self.weitrans) for w in self.w])
        if self.textrans is not None:
            data.append(max(0, round(float(self.u) * self.textrans)))
            data.append(max(0, round(float(self.v) * self.textrans)))
        if self.color_trans is not None:
            data.append(self.color)  # color_trans
        if self.nortrans is not None:
            data.append(round(float(self.i) * self.nortrans))
            data.append(round(float(self.j) * self.nortrans))
            data.append(round(float(self.k) * self.nortrans))
        if self.postrans is not None:
            data.append(round((float(self.x) / self.scale["x"]) * self.postrans))
            data.append(round((float(self.y) / self.scale["y"]) * self.postrans))
            data.append(round((float(self.z) / self.scale["z"]) * self.postrans))
        return struct.pack(self.verfor, *data)

    def write(self, file) -> None:
        file.seek(self.address)
        file.write(self.to_pmo())

    def set_scale(self, newscale: dict) -> None:
        self.scale = newscale


class Index(PMODATA):
    def __init__(self, ind_format: str | None) -> None:
        super().__init__()
        self.format: str | None = ind_format
        self.vertices: list = []
        self.face_order: None | int = 0 if ind_format is None else None
        self.primative_type: None | int = 4 if ind_format is None else None
        self.index_offset: None | int = 0 if ind_format is None else None

    def __iter__(self) -> iter:
        return self.vertices.__iter__()

    def tobytes(self) -> bytes:
        if self.format is None:
            return b''
        byted = b''
        for x in self.vertices:
            byted += struct.pack(self.format, x)

        return byted

    def to_faces(self) -> list:
        faces = []

        r = range(len(self.vertices)-2)
        if self.primative_type == 3:
            r = range(0, len(self.vertices), 3)

        for vert in r:
            face = {3: self.vertices[vert + 2] + self.index_offset}
            if ((vert + self.face_order) % 2) or ((self.primative_type == 3) and self.face_order):
                face[2] = self.vertices[vert] + self.index_offset
                face[1] = self.vertices[vert + 1] + self.index_offset
            else:
                face[1] = self.vertices[vert] + self.index_offset
                face[2] = self.vertices[vert + 1] + self.index_offset
            faces.append(face)

        return faces

BYTE = 1
SHORT = 2
FLOAT = 3

class VertexFormat:
    def __init__(self, weight_f: int | None = BYTE, uv_f: int | None = SHORT, color_f: int | None = None, normal_f: int | None = BYTE, 
                 position_f: int | None = SHORT, weight_count: int = 0, bypass_transform: int = 0) -> None:
        self.weight_f: int | None = weight_f
        self.uv_f: int | None = uv_f
        self.color_f: int | None = color_f
        self.normal_f: int | None = normal_f
        self.position_f: int | None = position_f
        self.weight_count: int = weight_count
        self.bypass_transform: int = bypass_transform

    @property
    def struct(self) -> str:
        str_format = ""
        if self.weight_f is not None:
            str_format += f'{self.weight_count}{["", "B", "H", "f"][self.weight_f]}'
        if self.uv_f is not None:
            str_format += ["", "2B", "2H", "2f"][self.uv_f]
        if self.color_f is not None:
            str_format += ["", "", "", "", "", "", "H", "I"][self.color_f]
        if self.normal_f is not None:
            str_format += ["", "3b", "3h", "3f"][self.normal_f]
        if self.bypass_transform:
            str_format += ["", "2bB", "2hH", "3f"][self.position_f]
        else:
            str_format += ["", "3b", "3h", "3f"][self.position_f]
        
        return str_format


class Mesh(PMODATA):
    def __init__(self) -> None:
        super().__init__()
        self.tri_header: None | TristripHeader = None
        self.vertex_format: None | VertexFormat = None
        self.index_format: None | str = None
        self.vertices: None | list[Vertex] = None
        self.indices: None | list[Index] = None
        self.base_offset: None | int = None
        self.bypass_transform: int = 0

        self.face_order: None | int = None

    @property
    def max_index(self) -> int:
        return max(0, *[max(index) for index in self.indices])

    @property
    def faces(self) -> list:
        faces = []
        for index in self.indices:
            faces.extend(index.to_faces())
        return faces

    @property
    def vtype(self) -> int:
        command = 0x12000000  # Base vtype command
        command |= self.bypass_transform << 23  # Bypass Transform

        command |= max(0, self.tri_header.weightCount - 1 << 14)  # Weight Count
        if self.tri_header.bones:
            command |= self.vertex_format.weight_f << 9  # Weight Format
        if self.vertices[0].textrans is not None:
            command |= self.vertex_format.uv_f  # UV Format
        if self.vertices[0].color_trans is not None:
            command |= self.vertex_format.color_f << 2  # Color Format
        if self.vertices[0].nortrans is not None:
            command |= self.vertex_format.normal_f << 5  # Normal Format
        command |= self.vertex_format.position_f << 7  # Position Format

        command |= {None: 0, 'B': 1, 'H': 2, 'I': 3}[self.index_format] << 11  # Index Format

        return command if command > 0 else command+2**32

    def write(self, fd) -> None:
        fd.seek(self.address)
        fd.write(self.to_pmo())

    @property
    def vertex_data(self) -> bytes:
        byted = b''
        vert: Vertex
        for vert in self.vertices:
            byted += vert.to_pmo()

        return byted

    @property
    def index_data(self) -> bytes:
        byted = b''
        index: Index
        for index in self.indices:
            byted += index.tobytes()
        return byted

    @property
    def prims(self) -> bytes:
        prims = b''
        if self.tri_header.alpha_blend:
            prims += b'\x01\x00\x00\x21'  # enable alpha blending
            prims += b'\x07\x05\xFF\xdb'  # set alpha test parameters
        
        face_order = None
        #prims += struct.pack("I", (1 if self.tri_header.backface_culling else 0) | 0x1D000000)
        index: Index
        for index in self.indices:
            if index.face_order != face_order:
                face_order = index.face_order
                prims += struct.pack("I", face_order | 0x9B000000)

            prim = 0x04000000
            prim |= index.primative_type << 16
            prim |= len(index.vertices)

            prims += struct.pack("I", prim)
        
        if self.tri_header.alpha_blend:
            prims += b'\x00\x00\x00\x21'  # disable alpha blending
        
        if self.tri_header.backface_culling:
            prims += struct.pack("I", 0x1D000000)  # disable backface culling
        
        return prims

    @property
    def vaddr(self) -> int:
        vaddr = 0x1C + len(self.prims)
        if vaddr % 8:
            vaddr += vaddr % 8
        return vaddr

    @property
    def iaddr(self) -> int:
        if self.index_format is None:
            return 0
        iaddr = self.vaddr + len(self.vertices) * struct.calcsize(self.vertex_format.struct)
        if iaddr % 8:
            iaddr += iaddr % 8
        return iaddr

    def to_pmo(self, newfile=False) -> bytes:
        start = (b'\x00\x00\x00\x14'
                 b'\x00\x00\x00\x10')

        vtype = struct.pack("I", self.vtype)

        vaddr = self.vaddr
        if not newfile:
            vaddr = self.vertices[0].address - self.address

        iaddr = self.iaddr
        if not newfile:
            iaddr = self.indices[0].address - self.address

        addresses = ((struct.pack("I", iaddr | 0x02000000) if self.index_format is not None else b'') +
                     struct.pack("I", vaddr | 0x01000000))

        byted = start + addresses + vtype + self.prims + b'\x00\x00\x00\x13\x00\x00\x00\x0B'

        if newfile:
            if len(byted) < vaddr:
                byted += bytes(vaddr - len(byted))
            byted += self.vertex_data
            if len(byted) < iaddr:
                byted += bytes(iaddr - len(byted))
            byted += self.index_data
            byted += bytes(len(byted) % 4)

        return byted


class PMO:
    def __init__(self) -> None:
        self.header = PMOHeader()
        self.mat_remaps: list[int] = []
        self.mesh_header: list[MeshHeader] = []

    def __repr__(self) -> str:
        string = (f'\nMeshes: {len(self.mesh_header)}\n'
                  f'Materials: {len(self.materials)}\n'
                  f'Vertices: {len(self.vertices)}\n')
        return repr(self.header) + string

    @property
    def meshes(self) -> list[Mesh]:
        meshes = []
        for meshHeader in self.mesh_header:
            meshes.extend(meshHeader.meshes)

        return meshes

    @property
    def materials(self) -> list[Material]:
        materials = []
        for meshHeader in self.mesh_header:
            materials.extend(meshHeader.materials)

        return materials

    @property
    def tristrips(self) -> list[TristripHeader]:
        tristrips = []
        for mesh in self.meshes:
            tristrips.append(mesh.tri_header)

        return tristrips

    @property
    def ver(self) -> bytes:
        return self.header.ver

    @property
    def mat_remap_data(self) -> bytes:
        byted = b''
        if self.ver != FU_MODEL:
            return byted
        for x in self.mat_remaps:
            byted += struct.pack("b", x)  # [0]
        if len(byted) < 0x10:
            byted += bytes(0x10 - len(byted))
            return byted
        if len(byted) % 0x10:
            byted += bytes(len(byted) % 0x10)
        return byted

    @property
    def faces(self) -> list:
        faces = []
        for index in self.indexes:
            faces.extend(index.to_faces())
        return faces

    @property
    def indexes(self) -> list:
        indexes = []
        mesh: Mesh
        for mesh in self.meshes:
            indexes.extend(mesh.indices)
        return indexes

    @property
    def vertices(self) -> list:
        vertices = []
        mesh: Mesh
        for mesh in self.meshes:
            vertices.extend(mesh.vertices)
        return vertices

    def fix_scales(self) -> None:
        maxx = max(max([vert.x for vert in self.vertices]),
                   -1*min([vert.x for vert in self.vertices]), self.header.scale["x"])
        maxy = max(max([vert.y for vert in self.vertices]),
                   -1 * min([vert.y for vert in self.vertices]), self.header.scale["y"])
        maxz = max(max([vert.z for vert in self.vertices]),
                   -1 * min([vert.z for vert in self.vertices]), self.header.scale["z"])
        abs_max = max(maxx, maxy, maxz)
        self.header.clippingDistance = abs_max
        new_scale = {
            "x": abs_max,
            "y": abs_max,
            "z": abs_max,
        }
        if self.header.scale == {"x": 0.0, "y": 0.0, "z": 0.0}:
            self.header.scale = new_scale
        for mesh in self.mesh_header:
            mesh.set_scale(new_scale)
        for vert in self.vertices:
            vert.set_scale(new_scale)

    @property
    def bone_data(self) -> bytes:
        # TODO: Update bone data for fu models, tho it shouldn't be a problem
        data = b''
        tri: TristripHeader
        for tri in self.tristrips:
            data += tri.bone_data
        if len(data) < 0x10:
            data += bytes(0x10 - len(data))
        if len(data) % 8:  # Might be 16
            data += bytes(len(data) % 8)

        return data

    def write(self, file) -> None:
        self.header.write(file)
        # Write bone data
        file.seek(self.header.boneDataOffset)
        file.write(self.bone_data)
        # Write mesh headers
        for mesh in self.mesh_header:
            mesh.write(file)
        # Write mesh data
        for mesh in self.meshes:
            mesh.write(file)
        # Write tristrip headers
        tristrip: TristripHeader
        for tristrip in self.tristrips:
            tristrip.write(file)
        # write vertex data
        vert: Vertex
        for vert in self.vertices:
            vert.write(file)
        for mat in self.materials:
            mat.write(file)
        for index in self.indexes:
            index.write(file)
        # Write fu mat remap data
        if self.ver == FU_MODEL:
            file.seek(self.header.materialRemapOffset)
            file.write(self.mat_remap_data)

    def update(self) -> None:
        self.header.move(0)

        self.fix_scales()

        self.header.meshCount = len(self.mesh_header)
        self.header.materialCount = len(self.materials)

        self.header.meshHeaderOffset = 64
        total_tri_count = 0
        total_mat_count = 0
        for mesh_header in range(len(self.mesh_header)):
            mheader = self.mesh_header[mesh_header]
            mheader.move(self.header.meshHeaderOffset + self.mesh_header[0].size*mesh_header)
            mheader.update()
            mheader.cumulativeMaterialCount = total_mat_count
            mheader.cumulativeTristripCount = total_tri_count
            total_mat_count += mheader.materialCount
            total_tri_count += mheader.tristripCount

        self.header.tristripHeaderOffset = self.header.meshHeaderOffset + self.mesh_header[0].size*len(self.mesh_header)
        if self.header.tristripHeaderOffset % 16:
            self.header.tristripHeaderOffset += 16 - self.header.tristripHeaderOffset % 16
        for tri_header in range(len(self.tristrips)):
            self.tristrips[tri_header].move(self.header.tristripHeaderOffset + self.tristrips[0].size*tri_header)

        if self.ver == FU_MODEL:
            self.mat_remaps = list(range(len(self.materials)))
            self.header.materialRemapOffset = (self.header.tristripHeaderOffset + self.tristrips[0].size *
                                               len(self.tristrips))
            self.header.boneDataOffset = self.header.materialRemapOffset + len(self.mat_remap_data)
        else:
            self.header.boneDataOffset = (self.header.tristripHeaderOffset + self.tristrips[0].size *
                                          len(self.tristrips))

        self.header.materialDataOffset = self.header.boneDataOffset + len(self.bone_data)
        for mat in range(len(self.materials)):
            self.materials[mat].move(self.header.materialDataOffset + self.materials[0].size*mat)

        self.header.meshDataOffset = self.header.materialDataOffset + self.materials[0].size*len(self.materials)
        offset = 0
        mesh: Mesh
        for mesh in self.meshes:
            while (self.header.meshDataOffset + offset) % 8:
                offset += 1
            mesh.move(self.header.meshDataOffset + offset)
            mesh.tri_header.vertexOffset = mesh.vaddr + offset
            mesh.tri_header.meshOffset = offset
            mesh.tri_header.indexOffset = mesh.iaddr + offset
            offset += len(mesh.to_pmo(newfile=True))

        self.header.filesize = self.header.meshDataOffset + offset

    def save(self, fd, second=None) -> None:
        self.update()

        self.header.write(fd)
        # Write bone data
        fd.seek(self.header.boneDataOffset)
        print(self.bone_data)
        fd.write(self.bone_data)
        # Write mesh headers
        for mesh_he in self.mesh_header:
            mesh_he.write(fd)
        # Write tristrip headers
        tristrip: TristripHeader
        for tristrip in self.tristrips:
            tristrip.write(fd)
        for mat in self.materials:
            mat.write(fd)
        # Write mesh data
        if second is not None:
            for mesh in self.meshes:
                second.seek(mesh.address-self.header.meshDataOffset)
                second.write(mesh.to_pmo(newfile=True))
        else:
            mesh: Mesh
            for mesh in self.meshes:
                fd.seek(mesh.address)
                fd.write(mesh.to_pmo(newfile=True))

        # Write fu mat remap data
        if self.ver == FU_MODEL:
            fd.seek(self.header.materialRemapOffset)
            fd.write(self.mat_remap_data)
