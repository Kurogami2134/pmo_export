import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from io_scene_pmoexport import export_pmo


FU_MODEL = b'1.0\x00'
P3RD_MODEL = b'102\x00'

def export(context, filepath: str, version: str, target: 0, prepare_pmo: bool = False):
    ver = P3RD_MODEL if version == "1.2" else FU_MODEL
    pmo = export_pmo.export(ver, target, prepare_pmo)
    if not isinstance(pmo, int):
        f = open(filepath, 'wb')
        pmo.save(f)
        f.close()

    return {'FINISHED'}


class ExportPmo(Operator, ExportHelper):
    """Export Monster Hunter PMO models."""
    bl_idname = "export_mh.pmo"
    bl_label = "Export PMO"

    filename_ext = ".pmo"

    filter_glob: StringProperty(
        default="*.pmo",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    type: EnumProperty(
        name="Format Version",
        description="Choose pmo format version",
        items=(
            ('1.0', "MHFU", "Export MHFU models"),
            ('1.2', "MHP3rd", "Export MHP3rd models"),
        ),
        default='1.2',
    )

    export_target: EnumProperty(
        name="Export target",
        description="Select target for exporting",
        items=(
            ("scene", "Scene", "Export all mesh objects in the scene"),
            ("visible", "Visible", "Export all visible mesh objects"),
            ("selection", "Selection", "Export all selected mesh objects"),
            ("active", "Active", "Export active mesh object")
        ),
        default="visible",
    )

    prep_pmo: BoolProperty(
        name="Prepare PMO",
        description="Fix UVs for pmo before exporting. (Same as pressing 'Prepare PMO' but won't have a permanent effect on the model)",
        default=False
    )

    def execute(self, context):
        return export(context, self.filepath, self.type, self.export_target, self.prep_pmo)


def menu_func_export(self, context):
    self.layout.operator(ExportPmo.bl_idname, text="PSP MH PMO")


def register():
    bpy.utils.register_class(ExportPmo)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportPmo)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
