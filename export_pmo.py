import bpy
import bmesh
from . import model as pmodel
from .prep_pmo import xenthos_prep_pmo, asterisk_prep_pmo

try:
    from pyffi.utils import trianglestripifier
except:
    from subprocess import check_output
    import sys

    check_output([sys.executable, '-m', 'pip', 'install', 'pyffi', f'--target={bpy.utils.user_resource("SCRIPTS", path="modules")}'])
    from pyffi.utils import trianglestripifier


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
                groups[g] = groups[g] + [v] if g in groups else [v]
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


def pmo_material(material, tex: int | None = None):
    pmaterial = pmodel.Material()

    pmaterial.diffuse = {
        "r": material.pmo_diffuse[0] * 255,
        "g": material.pmo_diffuse[1] * 255,
        "b": material.pmo_diffuse[2] * 255,
        "a": material.pmo_diffuse[3] * 255
    }
    pmaterial.ambient = {
        "r": material.pmo_ambient[0] * 255,
        "g": material.pmo_ambient[1] * 255,
        "b": material.pmo_ambient[2] * 255,
        "a": material.pmo_ambient[3] * 255
    }
    pmaterial.textureIndex = material.pmo_texture_index if tex is None else tex

    return pmaterial

def warning(messages: list[str] = [""], title: str = "Warning"):
    def draw(self, context):
        for message in messages:
            self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon="ERROR")

def mat_tex(mat):
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            return node
    return -1

def export(pmo_ver: bytes, target: str = 'scene', prepare_pmo: str = "none", cleanup_vg: bool = False, get_textures: bool = False, apply_modifiers: bool = False, hard_tristripification: bool = False) -> tuple[pmodel.PMO | int, list | None]:
    try:
        print("Exporting PMO...")

        pmo = pmodel.PMO()
        pmo.header.ver = pmo_ver
        warnings = []

        match target:
            case "scene":  # scene
                objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
            
            case "visible":  # visible
                objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_get()]

            case "selection":  # selection
                objs = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.select_get()]

            case "active":  # active
                objs = [bpy.context.active_object]

        # Deselect every object
        for obj in bpy.data.objects:
            obj.select_set(False)

        if len(objs) == 0:
            warning(["No valid meshes found"])
            return -1, None

        cumulativeWeightCount = 0
        materials: dict[str, int] = {}
        pmo_mats: list[pmodel.Material] = []
        textures: list = []
        texture_indices: dict[str, int] = {}
        
        for base_obj in objs:
            obj = base_obj.copy()
            obj.data = base_obj.data.copy()
            obj.hide_set(False)
            bpy.context.collection.objects.link(obj)

            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

            if apply_modifiers:
                bpy.ops.object.convert(target="MESH")

            if cleanup_vg:
                bpy.ops.object.vertex_group_clean(group_select_mode="ALL")

            if len([v for v in obj.data.vertices if len(v.groups) == 0]):
                warnings.append(f'Object "{base_obj.name}" has vertices that are not tied to any vertex group and those will not be exported.')

            match prepare_pmo:
                case "xenthos":
                    xenthos_prep_pmo(obj)
                case "*&":
                    asterisk_prep_pmo(obj)
                case _:
                    pass

            sort_vertices(obj)

            mesh_header = pmodel.MeshHeader() if pmo_ver == pmodel.P3RD_MODEL else pmodel.FUMeshHeader()
            mesh_header.materialCount = len(obj.material_slots)
            mesh_header.tristripCount = len(obj.vertex_groups)

            if "PMO Alpha Blending Params" in obj:
                mesh_header.alpha_blending_params = obj["PMO Alpha Blending Params"]
            
            if "PMO Light Distance Attenuation Factor" in obj:
                mesh_header.ld_at_factor_c = obj["PMO Light Distance Attenuation Factor"]

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

            print("Constructing materials...")
            mesh_header.materials = []
            for mat in obj.data.materials:
                if mat.name not in materials:
                    mat_id = int(mat.name.split("_")[-1]) if "_" in mat.name else len(materials)
                    materials[mat.name] = mat_id
                    tex = None
                    if get_textures:
                        if not mat.pmo_overwrite_texture_index:
                            texture = mat_tex(mat)
                            if texture != -1:
                                if texture.image.name not in texture_indices:
                                    texture_indices[texture.image.name] = len(textures)
                                    textures.append(texture)
                                tex = texture_indices[texture.image.name]
                    pmo_mats.append((mat_id, pmo_material(mat, tex=tex)))
                    
            # *&'s code for mats and pmo attributes
            metalayers = list(filter(lambda x: "PMO " in x.name,obj.data.attributes))
            facetuples = list(zip(map(lambda x: materials[obj.data.materials[x.material_index].name], obj.data.polygons),
                                *map(lambda x: map(lambda y: y.value, x.data), metalayers)))
            metamats = {tp:[] for tp in sorted(list(set(facetuples)))}
            labels = list(map(lambda x: x.name.replace("PMO ",""), metalayers))
            for ix,face in enumerate(obj.data.polygons):
                metamats[facetuples[ix]].append(list(face.vertices))

            ready = []
            for props, face_collection in metamats.items():
                tris = {}
                me = trianglestripifier.Mesh(faces=face_collection)
                tristripifier = trianglestripifier.TriangleStripifier(me)
                tristrips = tristripifier.find_all_strips()  # indices

                for tri in tristrips:
                    bones = set()
                    for x in [[x.group for x in obj.data.vertices[v].groups] for v in tri]:
                        for bone in x:
                            bones.add((int(bpy.context.active_object.vertex_groups[bone].name.split(".")[-1]), obj.vertex_groups[bone].index))
                    bones = tuple(bones)
                    tris[bones] = tris[bones] + [tri] if bones in tris.keys() else [tri]
                
                # Join all tristrips
                if hard_tristripification:
                    for bones, tristrips in tris.items():
                        stripest: list = []
                        if len(tristrips) > 1:
                            tristrips = sorted(tristrips)
                            for strip in range(len(tristrips)):
                                if len(stripest) > 0 and len(stripest) % 2 == 0:
                                    stripest.append(stripest[-1])
                                if strip < len(tristrips) - 1:
                                    tristrips[strip].append(tristrips[strip][-1])
                                new = [tristrips[strip][0]] if strip > 0 else []
                                new.extend(tristrips[strip])
                                stripest.extend(new)
                        else:
                            stripest = tristrips[0]
                        tris[bones] = [stripest]

                ready.append(({k: v for k, v in zip(["material"] + labels, props)}, tris))

            uvs = {}
            for face in obj.data.polygons:
                for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                    if vert_idx not in uvs:
                        uvs[vert_idx] = [*obj.data.uv_layers.active.data[loop_idx].uv]
            
            obj.data.calc_tangents()
            
            normals = {}
            warn_multiple_normal = False
            for l in obj.data.loops:
                if l.vertex_index not in normals:
                    normals[l.vertex_index] = l.normal
                else:
                    warn_multiple_normal = warn_multiple_normal or (normals[l.vertex_index] != l.normal)
            
            if warn_multiple_normal:
                warnings.append(f'Because of some vertex having multiple normals, exported normals may not look as they do in the editor for "{base_obj.name}".')

            meshes = []
            print("Creating meshes...")
            for mesh in ready:
                print("Creating mesh...")
                props = mesh[0]
                for (bones, tri) in mesh[1].items():  # tri header/submesh creation
                    tristrip_header = pmodel.TristripHeader()
                    tristrip_header.materialOffset = props["material"]
                    print(tristrip_header.materialOffset, [id for id, index in bones])
                    tristrip_header.cumulativeWeightCount = cumulativeWeightCount
                    tristrip_header.weightCount = len(bones)
                    cumulativeWeightCount += tristrip_header.weightCount
                    tristrip_header.bones = [id for id, index in bones]
                    
                    if "Backface Culling" in props:
                        tristrip_header.backface_culling = props["Backface Culling"] > 0
                    if "Alpha Test Enable" in props:
                        tristrip_header.alpha_blend = props["Alpha Test Enable"] > 0
                    if  "Shade Flat" in props:
                        tristrip_header.shade_flat = props["Shade Flat"]
                    if "Texture Filter" in props:
                        tristrip_header.custom_tex_filter = True
                        tristrip_header.texture_filter = props["Texture Filter"]

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

                    verts = []
                    for x in tri:
                        verts.extend(x)
                    vert_remap = {v: k for k, v in enumerate(sorted(set(verts)))}

                    max_index = max(0, *[max(x) for x in tri])
                    me.index_format = "B" if max_index <= 255 else "H" if max_index <= 0xFFFF else "I"
                    me.indices = []
                    
                    for ind in tri:
                        index = pmodel.Index(me.index_format)
                        index.vertices = [vert_remap[v] for v in ind]
                        index.primative_type = 4  # tristrip mode
                        index.index_offset = 0
                        index.face_order = 0
                        me.indices.append(index)

                    me.vertices = []

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

        # Adding materials
        for _, mat in sorted(pmo_mats, key=lambda x: x[0]):
            pmo.materials.append(mat)
        print(pmo.materials)

        print("Export finished!\n\n")

        if warnings:
            warning(warnings)

        return (pmo, None) if not get_textures else (pmo, textures)
    except ValueError:
        warning(["Mesh is not triangulated."], "Error")
        return -1, None
