import bpy
import bmesh
from pyffi.utils import trianglestripifier
from io_scene_pmoexport import model as pmodel


def sort_vertices(obj):
    print("Sorting vertices...")
    bpy.ops.object.mode_set(mode='EDIT')
    me = obj.data
    bm = bmesh.from_edit_mesh(me)
    bmv = bm.verts
    bmv.ensure_lookup_table()

    mats = []
    for mat in obj.data.materials:
        mats.append([list(face.vertices) for face in obj.data.polygons if face.material_index == len(mats)])
    verts = []
    for x in mats:
        vs = set()
        for face in x:
            for v in face:
                vs.add(v)

        groups = {}
        for v in vs:
            for g in [g.group for g in me.vertices[v].groups]:
                groups[g] = groups[g] + [v] if g in groups.keys() else [v]
        verts.append(groups)

    ind = 0
    for mat in verts:
        for g in mat.values():
            for v in g:
                bmv[v].index = ind
                ind += 1
    bm.verts.sort()

    bmesh.update_edit_mesh(me)
    bpy.ops.object.mode_set(mode='OBJECT')


def pmo_material(material):
    pmaterial = pmodel.Material()

    pmaterial.rgba = {
        "r": material.rgba[0] * 255,
        "g": material.rgba[1] * 255,
        "b": material.rgba[2] * 255,
        "a": material.rgba[3] * 255
    }
    pmaterial.rgba2 = {
        "r": material.shadow_rgba[0] * 255,
        "g": material.shadow_rgba[1] * 255,
        "b": material.shadow_rgba[2] * 255,
        "a": material.shadow_rgba[3] * 255
    }
    pmaterial.textureIndex = material.texture_index

    return pmaterial


def export(pmo_ver: bytes):
    print("Exporting PMO...")

    pmo = pmodel.PMO()
    pmo.header.ver = pmo_ver

    bpy.ops.object.mode_set(mode='OBJECT')
    obj = bpy.context.active_object

    sort_vertices(obj)

    mesh_header = pmodel.MeshHeader() if pmo_ver == pmodel.P3RD_MODEL else pmodel.FUMeshHeader()
    mesh_header.materialCount = len(obj.material_slots)
    mesh_header.tristripCount = len(obj.vertex_groups)

    # Scale definition
    maxx = max(max([vert.co.x for vert in obj.data.vertices]),
               -1 * min([vert.co.x for vert in obj.data.vertices]))
    maxy = max(max([vert.co.y for vert in obj.data.vertices]),
               -1 * min([vert.co.y for vert in obj.data.vertices]))
    maxz = max(max([vert.co.z for vert in obj.data.vertices]),
               -1 * min([vert.co.z for vert in obj.data.vertices]))
    abs_max = max(maxx, maxy, maxz)
    scale = {"x": abs_max, "y": abs_max, "z": abs_max}
    if pmo_ver == pmodel.P3RD_MODEL:
        mesh_header.scale = scale
    else:
        mesh_header.uvscale = {"u": 1, "v": 1}

    mats = []
    for mat in obj.data.materials:
        mats.append([list(face.vertices) for face in obj.data.polygons if face.material_index == len(mats)])
        mesh_header.materials.append(pmo_material(mat))

    ready = []
    for material in range(len(mats)):
        tris = {}
        me = trianglestripifier.Mesh(faces=mats[material])
        tristripifier = trianglestripifier.TriangleStripifier(me)
        tristrips = tristripifier.find_all_strips()  # indices

        for tri in tristrips:
            bones = set()
            for x in [[x.group for x in obj.data.vertices[v].groups] for v in tri]:
                for bone in x:
                    bones.add(obj.vertex_groups[bone].index)
            bones = tuple(bones)
            tris[bones] = tris[bones] + [tri] if bones in tris.keys() else [tri]
        ready.append((material, tris))

    uvs = {}
    for face in obj.data.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            if vert_idx not in uvs.keys():
                uvs[vert_idx] = [*obj.data.uv_layers.active.data[loop_idx].uv]

    meshes = []
    print("Creating meshes...")
    for mesh in ready:
        for (bones, tri) in zip(mesh[1].keys(), mesh[1].values()):  # tri header creation
            tristrip_header = pmodel.TristripHeader()
            tristrip_header.materialOffset = mesh[0]
            if len(meshes):
                tristrip_header.cumulativeWeightCount = meshes[-1].tri_header.weightCount + \
                                                        meshes[-1].tri_header.cumulativeWeightCount
            tristrip_header.weightCount = len(bones)
            tristrip_header.bones = list(bones)

            # mesh creation
            me = pmodel.Mesh()
            me.tri_header = tristrip_header
            me.vertex_format = f'{tristrip_header.weightCount}B2H3b3h'
            me.base_offet = 0

            min_index = min(3000, *[min(x) for x in tri])
            max_index = max(0, *[max(x) for x in tri]) - min_index
            me.index_format = "B" if max_index <= 255 else "H" if max_index <= 0xFFFF else "I"
            me.indices = []
            
            for ind in tri:
                index = pmodel.Index(me.index_format)
                index.vertices = [x-min_index for x in ind]
                index.primative_type = 4  # tristrip mode
                index.index_offset = 0
                index.face_order = 0
                me.indices.append(index)

            me.vertices = []

            verts = []
            for x in tri:
                verts.extend(x)

            print("Adding vertices...")
            for v_idx in sorted(set(verts)):
                vert = obj.data.vertices[v_idx]
                vertex = pmodel.Vertex()
                vertex.nortrans = 0x7f
                vertex.postrans = 0x7fff
                vertex.textrans = 0x8000
                vertex.weitrans = 0x80
                vertex.verfor = me.vertex_format

                vertex.coords(vert.co.x, vert.co.z, vert.co.y)
                vertex.vt(uvs[vert.index][0], 1 - uvs[vert.index][1])
                vertex.scale = scale
                vertex.vn(vert.normal.x, vert.normal.z, vert.normal.y)

                vertex.w = []
                for bone in bones:
                    if bone in [vg.group for vg in vert.groups]:
                        weight = [vg.weight for vg in vert.groups if vg.group == bone][0]
                        vertex.w.append(weight)
                    else:
                        vertex.w.append(0)

                me.vertices.append(vertex)

            meshes.append(me)

    mesh_header.meshes = meshes

    pmo.mesh_header.append(mesh_header)

    print("Export finished!\n\n")
    return pmo
