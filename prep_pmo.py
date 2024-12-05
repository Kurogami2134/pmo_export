import bpy
import bmesh

# Xenthos' prepare pmo

def xenthos_prep_pmo(obj) -> None:
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


# *&'s prepare pmo
def asterisk_prep_pmo(obj):
    def triangulate(mesh):
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.new()
        bm.from_mesh(mesh)

        bmesh.ops.triangulate(bm, faces=bm.faces)

        bpy.ops.object.mode_set(mode='OBJECT')
        bm.to_mesh(mesh)
        bm.free()

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    me = obj.data

    triangulate(me)
    
    # *&'s code to handle edges and repeated vertices
    
    bpy.ops.object.mode_set(mode='EDIT')
    solveSharpRepeatedUV(obj)
    bpy.ops.object.mode_set(mode='OBJECT')


def bad_iter(blenderCrap):
    i = 0
    while (True):
        try:
            yield(blenderCrap[i])
            i+=1
        except:
            return


def selectRepeated(bm):
    bm.verts.index_update()
    bm.verts.ensure_lookup_table()
    targetVert = set()
    for uv_layer in bad_iter(bm.loops.layers.uv):
        uvMap = {}
        for face in bm.faces:
            for loop in face.loops:
                uvPoint = tuple(loop[uv_layer].uv)
                if loop.vert.index in uvMap and uvMap[loop.vert.index] != uvPoint:
                    targetVert.add(bm.verts[loop.vert.index])
                else:
                    uvMap[loop.vert.index] = uvPoint
    return targetVert


def solveRepeatedEdge(mesh):
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.uv.seams_from_islands()
    #
    me = mesh.data    
    bm = bmesh.from_edit_mesh(me)
    for e in bm.edges:
        if e.seam:
            e.select = True    
    bmesh.update_edit_mesh(me)
    bpy.ops.mesh.edge_split()
    bpy.ops.mesh.select_all(action='DESELECT')


def solveRepeatedVertex(mesh):
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(mesh.data)
    oldmode = bm.select_mode
    bm.select_mode = {'VERT'}    
    targets = selectRepeated(bm)
    for target in targets:
        bmesh.utils.vert_separate(target,target.link_edges)
        bm.verts.ensure_lookup_table()    
    bpy.ops.mesh.select_all(action='DESELECT')
    bm.select_mode = oldmode
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    bmesh.update_edit_mesh(mesh.data) 
    mesh.data.update()       
    return

def solveRepeatedUV(mesh):
    solveRepeatedEdge(mesh)
    solveRepeatedVertex(mesh)

def solveSharpUV(mesh):
    obj = mesh
    me = obj.data
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(me)
    for e in bm.edges:
        if not e.smooth:
            e.select = True
    bpy.ops.mesh.edge_split()
    bpy.ops.mesh.select_all(action='DESELECT')
    bmesh.update_edit_mesh(me)
    return
        
def solveSharpRepeatedUV(mesh):
    solveSharpUV(mesh)
    solveRepeatedUV(mesh)
