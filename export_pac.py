from . import export_pmo
from . import export_skel
from .containers import TMH, PAC
from .model import P3RD_MODEL, FU_MODEL
from struct import pack

import bpy

def export(context, filepath: str, version: str, target: str = 'scene', prepare_pmo: str = "none", cleanup_vg: bool = False, p3rd_helmet: bool = False, face_flags: tuple[bool] | None = None, hairflags: int | None = None, phys_id: int | None = None, app_modifiers: bool = False, hard_tristripification: bool = False):
    pac = PAC()
    ver = P3RD_MODEL if version == "1.2" else FU_MODEL

    pmo, textures = export_pmo.export(ver, target, prepare_pmo, cleanup_vg, get_textures=True, apply_modifiers=app_modifiers, hard_tristripification=hard_tristripification)
    if isinstance(pmo, int):
        return {'CANCELLED'}
    
    f = pac.add()
    pmo.save(f)

    f = pac.add()
    
    skeleton = [obj for obj in bpy.data.objects if obj.type == "EMPTY" and not obj.parent][0]
    if skeleton.type == "EMPTY":
        bones = export_skel.bonesFromEmpties(skeleton)
    elif skeleton.type == "ARMATURE":
        export_skel.bonesFromArmature(skeleton)
    else:
        return {'CANCELLED'}
    
    if ver == P3RD_MODEL:
        export_skel.export_p3rd_skel(bones, f)
    elif ver == FU_MODEL:
        export_skel.export_fu_skel(bones, f)
    
    f = pac.add()
    tmh = TMH()
    for texture in textures:
        tmh.loadImg(texture)
    tmh.buildTMH(f)

    if p3rd_helmet:
        f  = pac.add()
        f.write(pack("<2HI", sum([2**p for p, v in enumerate(face_flags) if v]), hairflags, phys_id))

    pac.save(filepath)

    return {'FINISHED'}
