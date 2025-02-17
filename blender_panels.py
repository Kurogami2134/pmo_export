import bpy
from .prep_pmo import xenthos_prep_pmo, asterisk_prep_pmo

bpy.types.Material.pmo_diffuse = bpy.props.FloatVectorProperty(size=4, default=(1.0, 1.0, 1.0, 1.0), min=0, max=1,
                                                        subtype='COLOR', name='Diffuse')
bpy.types.Material.pmo_ambient = bpy.props.FloatVectorProperty(size=4, default=(0.5, 0.5, 0.5, 1.0), min=0, max=1,
                                                               subtype='COLOR', name='Ambient')
bpy.types.Material.pmo_texture_index = bpy.props.IntProperty(name='Texture Index', min=0)
bpy.types.Material.pmo_overwrite_texture_index = bpy.props.BoolProperty(name='Overwrite Generated Index', default=False)


class PMOMaterialPanel(bpy.types.Panel):
    bl_label = "PMO Material"
    bl_idname = "MATERIAL_PT_pmo_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        material = context.material

        if material is None:
            return

        layout = self.layout

        split = layout.split()

        col = split.column()
        col.prop(material, "pmo_diffuse")
        col = split.column()
        col.prop(material, "pmo_ambient")

        row = layout.row()
        row.prop(material, "pmo_texture_index")
        row.prop(material, "pmo_overwrite_texture_index")


class PreparePmoPanel(bpy.types.Panel):
    bl_label = "Prepare PMO"
    bl_idname = "OBJECT_PT_prepare_pmo"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw(self, context):
        layout = self.layout

        # obj = context.object

        row = layout.row()
        row.operator("object.asterisk_prepare_pmo")
        row.operator("object.xenthos_prepare_pmo")


class XePreparePmo(bpy.types.Operator):
    """Triangulate mesh and split vertex for normals/uvs."""
    bl_idname = "object.xenthos_prepare_pmo"
    bl_label = "Xenthos"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        xenthos_prep_pmo(context.active_object)
        return {'FINISHED'}

class AsPreparePmo(bpy.types.Operator):
    """Triangulate mesh and split vertex for normals/uvs."""
    bl_idname = "object.asterisk_prepare_pmo"
    bl_label = "*&"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        asterisk_prep_pmo(context.active_object)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(PMOMaterialPanel)
    bpy.utils.register_class(PreparePmoPanel)
    bpy.utils.register_class(XePreparePmo)
    bpy.utils.register_class(AsPreparePmo)


def unregister():
    bpy.utils.unregister_class(PMOMaterialPanel)
    bpy.utils.unregister_class(PreparePmoPanel)
    bpy.utils.unregister_class(XePreparePmo)
    bpy.utils.unregister_class(AsPreparePmo)


if __name__ == "__main__":
    register()
