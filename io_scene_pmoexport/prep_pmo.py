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


def prep_pmo(obj):
    bpy.ops.object.mode_set(mode='OBJECT')
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
    else:
        return
    
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
