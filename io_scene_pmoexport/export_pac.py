from io_scene_pmoexport import export_pmo
from io_scene_pmoexport import export_skel
from io_scene_pmoexport.containers import TMH, PAC
from io_scene_pmoexport.model import P3RD_MODEL, FU_MODEL

import bpy

def export(context, filepath: str, version: str, target: str = 'scene', prepare_pmo: bool = False, cleanup_vg: bool = False):
    pac = PAC()
    ver = P3RD_MODEL if version == "1.2" else FU_MODEL

    pmo, textures = export_pmo.export(ver, target, prepare_pmo, cleanup_vg, get_textures=True)
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

    pac.save(filepath)

    return {'FINISHED'}
