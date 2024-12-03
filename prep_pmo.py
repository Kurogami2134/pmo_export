import bpy
import bmesh

# Xenthos' prepare pmo

def prep_pmo(obj) -> None:
    def triangulate(obj):
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    duplicate = obj.copy()
    duplicate.data = obj.data.copy()
    bpy.context.collection.objects.link(duplicate)
    bpy.context.view_layer.objects.active = obj

    triangulate(obj)

    # Step 3: Apply normal-related modifiers on original objects
    for mod_name in [m.name for m in obj.modifiers if m.type in {'WEIGHTED_NORMAL', 'NORMAL_EDIT'}]:
        bpy.ops.object.modifier_apply(modifier=mod_name)

    # Step 4: On original meshes, restore UV seams from islands
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.seams_from_islands()

    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bm = bmesh.from_edit_mesh(obj.data)
    edges_to_split = [edge for edge in bm.edges if edge.seam or not edge.smooth]

    # Perform edge split without duplicating vertices unnecessarily
    bmesh.ops.split_edges(bm, edges=edges_to_split)
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.object.mode_set(mode='OBJECT')

    # Step 6: Add Data Transfer modifier and apply
    modifier = obj.modifiers.new(name="DataTransfer", type='DATA_TRANSFER')
    modifier.object = duplicate
    modifier.use_loop_data = True
    modifier.data_types_loops = {'CUSTOM_NORMAL'}
    bpy.ops.object.modifier_apply(modifier="DataTransfer")

    # Step 7: Clear any extra sharp edges added as a result of Data Transfer
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Select all faces, clear sharp, and clear seams
    bm = bmesh.from_edit_mesh(obj.data)
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.mark_sharp(clear=True)
    bpy.ops.mesh.mark_seam(clear=True)
    bmesh.update_edit_mesh(obj.data)

    # Deselect all faces
    bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(duplicate, do_unlink=True)
