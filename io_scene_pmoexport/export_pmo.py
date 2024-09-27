import bpy
import bmesh
from io_scene_pmoexport import model as pmodel
from io_scene_pmoexport.fix_uvs import fix_uvs

try:
    from pyffi.utils import trianglestripifier
except:
    from subprocess import check_call
    check_call([bpy.app.binary_path_python, '-m', 'pip', 'install', 'pyffi'])
    from pyffi.utils import trianglestripifier


def fix_vg(obj):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="VERT")

    groups = sorted(obj.vertex_groups, key=lambda x:x.name)

    for idx, vg in enumerate(groups):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group=vg.name)
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_linked()
        bpy.ops.object.vertex_group_deselect()
        bpy.context.scene.tool_settings.vertex_group_weight = 0
        bpy.ops.object.vertex_group_assign()
        bpy.context.scene.tool_settings.vertex_group_weight = 1
        
        while vg.index > idx:
            bpy.ops.object.vertex_group_move(direction='UP')

    bpy.ops.object.mode_set(mode='OBJECT')


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

def warning(message: str = "", title: str = "Warning"):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon="ERROR")

def export(pmo_ver: bytes, target: int = 0, prepare_pmo: bool = False) -> pmodel.PMO | int:
    print("Exporting PMO...")

    pmo = pmodel.PMO()
    pmo.header.ver = pmo_ver

    match target:
        case "scene":  # scene
            objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
        
        case "visible":  # visible
            objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_get()]

        case "selection":  # selection
            objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.select]

        case "active":  # active
            objs = [bpy.context.active_object]

    if len(objs) == 0:
        warning("No valid meshes found")
        return -1

    cumulativeWeightCount = 0
    
    for base_obj in objs:
        obj = base_obj.copy()
        obj.data = base_obj.data.copy()
        obj.hide_set(False)
        bpy.context.collection.objects.link(obj)

        bpy.context.view_layer.objects.active = obj

        if prepare_pmo:
            fix_uvs(obj)
        
        fix_vg(obj)

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

        print("Constructing materials...")
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
                        bones.add((int(bpy.context.active_object.vertex_groups[bone].name.split(".")[-1]), obj.vertex_groups[bone].index))
                        #bones.add(obj.vertex_groups[bone].index)
                bones = tuple(bones)
                tris[bones] = tris[bones] + [tri] if bones in tris.keys() else [tri]
            ready.append((material, tris))

        uvs = {}
        for face in obj.data.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                if vert_idx not in uvs.keys():
                    uvs[vert_idx] = [*obj.data.uv_layers.active.data[loop_idx].uv]
        
        obj.data.calc_tangents()
        
        normals = {}
        warn_multiple_normal = False
        for l in obj.data.loops:
            if l.vertex_index not in normals.keys():
                normals[l.vertex_index] = l.normal
            else:
                warn_multiple_normal = True
        
        if warn_multiple_normal:
            warning("Because of some vertex having multiple normals, exported normals may not look as in the editor.")

        meshes = []
        print("Creating meshes...")
        for mesh in ready:
            print("Creating mesh...")
            for (bones, tri) in mesh[1].items():  # tri header creation
                tristrip_header = pmodel.TristripHeader()
                tristrip_header.materialOffset = mesh[0]
                tristrip_header.cumulativeWeightCount = cumulativeWeightCount
                tristrip_header.weightCount = len(bones)
                cumulativeWeightCount += tristrip_header.weightCount
                tristrip_header.bones = [id for id, index in bones]
                tristrip_header.backface_culling = obj.data.materials[mesh[0]].use_backface_culling
                tristrip_header.alpha_blend = obj.data.materials[mesh[0]].blend_method == 'BLEND'

                # mesh creation
                me = pmodel.Mesh()
                me.tri_header = tristrip_header
                me.vertex_format = pmodel.VertexFormat(
                    weight_count = tristrip_header.weightCount,
                    weight_f = pmodel.BYTE,
                    uv_f = pmodel.SHORT,
                    normal_f = pmodel.BYTE,
                    position_f = pmodel.SHORT
                )

                me.base_offset = 0

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
                    vertex.verfor = me.vertex_format.struct

                    vertex.coords(vert.co.x, vert.co.y, vert.co.z)
                    vertex.vt(uvs[vert.index][0], 1 - uvs[vert.index][1])
                    vertex.scale = scale
                    vertex.vn(*normals[vert.index])
                    
                    vertex.w = []
                    for bone in [index for id, index in bones]:
                        print(type(bone))
                        if bone in [vg.group for vg in vert.groups]:
                            weight = [vg.weight for vg in vert.groups if vg.group == bone][0]
                            vertex.w.append(weight)
                        else:
                            vertex.w.append(0)

                    me.vertices.append(vertex)

                meshes.append(me)

        mesh_header.meshes = meshes

        pmo.mesh_header.append(mesh_header)
        
        bpy.data.objects.remove(obj, do_unlink=True)

    print("Export finished!\n\n")
    return pmo
