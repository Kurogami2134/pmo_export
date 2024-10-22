import bpy
from struct import pack


class PMOBone():
    def __init__(self, bone_id: int = 0, parent: int = 0, name: str = "", position: tuple[float, float, float] = (0.0, 0.0, 0.0),
                 scale: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> None:
        self.bone_id: int = bone_id
        self.parent: int = parent
        self.child: int = -1
        self.sibling: int = -1
        self.scale: tuple[float, float, float] = scale
        self.rotation: tuple[float, float, float] = (1.0, 1.0, 1.0)
        self.position: tuple[float, float, float] = position
        self.name: str = name
        self.chain_id: int = -1


def getFirstChild(idx: int, bones: dict[int, PMOBone]) -> int:
    for i, bone in bones.items():
        if bone.parent == idx:
            return bone.bone_id
    return -1


def fix_siblings(bones: dict[int, PMOBone]) -> None:
    parents = {}
    for i, bone in bones.items():
        if bone.parent == -1:
            continue
        
        if bone.parent in parents:
            parents[bone.parent].append(i)
        else:
            parents[bone.parent] = [i]
    
    for parent in parents:
        parents[parent] = zip(parents[parent], parents[parent][1:]+[-1])
    
    for parent in parents:
        for (child, sibling) in parents[parent]:
            print(parent, child, sibling)
            bones[child].sibling = sibling
            print(bones[child])


def getParent(child, ebs) -> int:
    if child.parent is None:
        return -1
    
    for idx, eb in enumerate(ebs):
        if child.parent == eb:
            return idx
    return -1


def export_p3rd_skel(bones: dict[int, PMOBone], path) -> None:
    rootbones = [bone.bone_id for idx, bone in bones.items() if bone.parent == -1]

    fix_siblings(bones)

    with open(path, "wb") as file:
        file.write(b'\x00\x00\x00\x80')
        file.write(pack("2I", len(bones)+1, 0x5c*len(bones) + len(rootbones)*4+12 + 12))
        file.write(pack(f'{len(rootbones)+3}I', 0, len(rootbones), len(rootbones)*4 + 12, *rootbones))
        bone_start_add = file.tell()
        for idx, bone in bones.items():
            file.seek(bone_start_add+bone.bone_id*0x5C)
            file.write(b'\x01\x00\x00\x40')
            file.write(pack("6i12f2i", 1, 0x5c, bone.bone_id, bone.parent, getFirstChild(idx, bones), bone.sibling, *bone.scale, 1.0, *[0.0]*3, 1.0, *bone.position, 1.0, -1, 0))
            name = bone.name.split(".")[0][:7].encode("utf-8")
            file.write(name)
            if len(name) < 8:
                file.write(bytes(8-len(name)))


def export_fu_skel(bones: dict[int, PMOBone], path) -> None:
    rootbones = [bone.bone_id for idx, bone in bones.items() if bone.parent == -1]
    bone_size = 0x48+12+4*46

    fix_siblings(bones)

    with open(path, "wb") as file:
        file.write(b'\x00\x00\x00\xC0')
        file.write(pack("2I", len(bones)+1, bone_size*len(bones) + len(rootbones)*4+12 + 12))
        file.write(pack(f'{len(rootbones)+3}I', 0, len(rootbones), len(rootbones)*4 + 12, *rootbones))
        bone_start_add = file.tell()
        for idx, bone in bones.items():
            file.seek(bone_start_add+bone.bone_id*bone_size)
            file.write(b'\x01\x00\x00\x40' +  pack("2i", 1, bone_size))
            file.write(pack("4i12fi", bone.bone_id, bone.parent, getFirstChild(idx, bones), bone.sibling, *bone.scale, 1.0, *[0.0]*3, 1.0, *bone.position, 1.0, -1))
            file.write(pack("i", bone.chain_id))
            file.write(bytes(4*46))  # padding?


def bonesFromArmature(obj) -> dict[int, (int, int, int, str)]:
    bpy.ops.object.mode_set(mode='EDIT')
    ebs = obj.data.edit_bones
    bones: dict[int, PMOBone] = {}

    for idx, eb in enumerate(ebs):
        parent = getParent(eb, ebs)
        bone_index = int(eb.name.split(".")[1])
        bones[idx] = PMOBone(bone_index, bones[parent].bone_id if parent >= 0 else -1, eb.name, tuple(eb.location), tuple(eb.scale))
    
    for idx, bone in reversed(bones.items()):
        if bone[1] >= 0:
            bones[idx].position = tuple(a-b for a, b in zip(bone.position, bones[bone.parent].position))
    
    return bones


def bonesFromEmpties(obj) -> dict[int, (int, int, int, str)]:
    ebs = []
    getChildren(ebs, obj)
    bones: dict[int, PMOBone] = {}

    for idx, eb in enumerate(ebs):
        parent = getParent(eb, ebs)
        bone_index = eb["id"]
        bones[idx] = PMOBone(bone_index, bones[parent].bone_id if parent >= 0 else -1, eb.name, tuple(eb.location), tuple(eb.scale))
        bones[idx].chain_id = eb["chain id"]
    
    return bones
   

def getChildren(ls, obj):
    ls.extend(obj.children)
    for child in obj.children:
        getChildren(ls, child)
