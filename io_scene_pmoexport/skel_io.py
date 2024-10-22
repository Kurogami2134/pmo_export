import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, EnumProperty

from io_scene_pmoexport import export_skel

def export(context, filepath: str, version: str):
    obj = bpy.context.active_object
    if obj.type == "EMPTY":
        bones = export_skel.bonesFromEmpties(obj)
    elif obj.type == "ARMATURE":
        export_skel.bonesFromArmature(obj)
    else:
        return {'CANCELLED'}
    
    if version == "p3rd":
        export_skel.export_p3rd_skel(bones, filepath)
    elif version == "fu":
        export_skel.export_fu_skel(bones, filepath)

    return {'FINISHED'}

class ExportPMOSkel(Operator, ExportHelper):
    """Export skeletal data for PSP Monster Hunter PMO models."""
    bl_idname = "export_psp_mh.skel"
    bl_label = "Export PMO SKEL"

    filename_ext = ".ahi"

    filter_glob: StringProperty(
        default="*.ahi",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    version: EnumProperty(
        name="Format Version",
        description="Choose ahi format version",
        items=(
            ('fu', "MHFU", "Export MHFU skeletons"),
            ('p3rd', "MHP3rd", "Export MHP3rd skeletons"),
        ),
        default='p3rd',
    )

    def execute(self, context):
        return export(context, self.filepath, self.version)


def menu_func_export(self, context):
    self.layout.operator(ExportPMOSkel.bl_idname, text="PSP MH AHI")


def register():
    bpy.utils.register_class(ExportPMOSkel)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportPMOSkel)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
