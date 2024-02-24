import bpy
import bmesh


def triangulate(mesh):
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.new()
    bm.from_mesh(mesh)

    bmesh.ops.triangulate(bm, faces=bm.faces)

    bpy.ops.object.mode_set(mode='OBJECT')
    bm.to_mesh(mesh)
    bm.free()


def uvs(vertex_index, me):
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = set([tuple(me.uv_layers.active.data[loop.index].uv) for loop in me.loops if loop.vertex_index == vertex_index])
    bpy.ops.object.mode_set(mode='EDIT')
    return uv


def fix_uvs():
    bpy.ops.object.mode_set(mode='OBJECT')
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    me = obj.data

    triangulate(me)

    a = None

    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            break

    with bpy.context.temp_override(area=a, space_data=a.spaces.active, region=a.regions[-1]):
        while max([len(uvs(x, me)) for x in range(len(me.vertices))]) > 1:
            for x in range(len(me.vertices)):
                while len(uvs(x, me)) > 1:
                    bpy.ops.object.mode_set(mode='OBJECT')
                    me.vertices[x].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.rip("INVOKE_DEFAULT")
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')
