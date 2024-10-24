import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from io_scene_pmoexport.export_pac import export

class ExportPac(Operator, ExportHelper):
    """Export Monster Hunter PAC files."""
    bl_idname = "export_mh.pac"
    bl_label = "Export PAC"

    filename_ext = ".pac"

    filter_glob: StringProperty(
        default="*.pac",
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
        description="Triangulate mesh and split vertex for normals/uvs. (Same as pressing 'Prepare PMO' but won't have a permanent effect on the model)",
        default=False
    )

    cleanup_vg: BoolProperty(
        name="Clean Up VG",
        description="Remove vertex group assignments wich are not required",
        default=False
    )

    def execute(self, context):
        return export(context, self.filepath, self.type, self.export_target, self.prep_pmo, self.cleanup_vg)

def menu_func_export(self, context):
    self.layout.operator(ExportPac.bl_idname, text="PSP MH PAC")

def register():
    bpy.utils.register_class(ExportPac)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportPac)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()