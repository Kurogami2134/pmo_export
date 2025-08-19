import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator, Panel

from .export_pac import export


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

    prep_pmo: EnumProperty(
        name="Prepare PMO",
        description="Triangulate mesh and split vertex for normals/uvs. (Same as pressing 'Prepare PMO' but won't have a permanent effect on the model)",
        items=(
            ("none", "None", "Do not run any prep script"),
            ("simple", "Simple", "Just split seams and sharp edges"),
            ("*&", "*&'s", "Run *&'s script"),
            ("xenthos", "Xenthos'", "Run Xenthos' script"),
        ),
        default="simple"
    )

    cleanup_vg: BoolProperty(
        name="Clean Up VG",
        description="Remove vertex group assignments wich are not required",
        default=False
    )

    do_fix_vg: BoolProperty(
        name="Merge Submeshes",
        description="Attempts to reduce submeshes by merging them based on material and bones",
        default=False
    )

    upper_face: BoolProperty(
        name="Forehead",
        default=True
    )

    lower_face: BoolProperty(
        name="Jaw",
        default=True
    )

    ears: BoolProperty(
        name="Ears",
        default=True
    )

    eyes: BoolProperty(
        name="Eyes",
        default=True
    )

    nose: BoolProperty(
        name="Nose",
        default=True
    )

    nape: BoolProperty(
        name="Nape",
        default=True
    )

    makeup1: BoolProperty(
        name="Makeup 1",
        default=True
    )

    makeup2: BoolProperty(
        name="Makeup 2",
        default=True
    )

    phys_id: IntProperty(
        name="Physics ID",
        default=0
    )

    hairflags: IntProperty(
        name="Hair Flags",
        description="Seems to be incomplete\nSCALP = 1\nFRONT = 2\nFRONT_2 = 4\nBACK_1 = 8\nBACK_2 = 16\nBACK_3 = 32",
        default=255
    )

    p3rd_helmet: BoolProperty(
        name="Is P3rd helmet",
        description="Export as p3rd helmet. Following properties are ignored if not",
        default=False
    )

    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers before exporting",
        default=False
    )

    hard_tristripification: BoolProperty(
        name="Hard Tristripification",
        description="Create as few tristrips as possible",
        default=False
    )

    def execute(self, context):
        face = (self.upper_face, self.ears, self.nape, self.lower_face, self.nose, self.eyes, self.makeup1, self.makeup2)
        return export(
            context,
            filepath=self.filepath,
            version=self.type,
            target=self.export_target,
            prepare_pmo=self.prep_pmo,
            cleanup_vg=self.cleanup_vg,
            p3rd_helmet=self.p3rd_helmet,
            face_flags=face,
            hairflags=self.hairflags,
            phys_id=self.phys_id,
            app_modifiers=self.apply_modifiers,
            hard_tristripification=self.hard_tristripification,
            do_fix_vg=self.do_fix_vg
        )
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation

        layout.prop(self, 'type')
        layout.prop(self, 'export_target')
        layout.prop(self, 'prep_pmo')
        layout.prop(self, 'cleanup_vg')
        layout.prop(self, 'apply_modifiers')
        layout.prop(self, 'hard_tristripification')


class FaceFlags(Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "P3rd Helmet"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_MH_OT_pac"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        row = layout.row()
        row.prop(operator, 'p3rd_helmet')
        row = layout.row()
        row.prop(operator, 'upper_face')
        row.prop(operator, 'lower_face')
        row = layout.row()
        row.prop(operator, 'nose')
        row.prop(operator, 'eyes')
        row = layout.row()
        row.prop(operator, 'ears')
        row.prop(operator, 'nape')
        row = layout.row()
        row.prop(operator, 'makeup1')
        row.prop(operator, 'makeup2')
        row = layout.row()
        row.prop(operator, 'hairflags')
        row = layout.row()
        row.prop(operator, 'phys_id')


def menu_func_export(self, context):
    self.layout.operator(ExportPac.bl_idname, text="PSP MH PAC")

classes = (
    ExportPac,
    FaceFlags
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()