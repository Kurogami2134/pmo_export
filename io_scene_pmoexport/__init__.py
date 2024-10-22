from io_scene_pmoexport import blender_panels
from io_scene_pmoexport import pmo_export_menu
from io_scene_pmoexport import skel_io

bl_info = {
    "name": "PMO Export",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}


def register():
    blender_panels.register()
    pmo_export_menu.register()
    skel_io.register()


def unregister():
    blender_panels.unregister()
    pmo_export_menu.unregister()
    skel_io.unregister()

if __name__ == "__main__":
    register()
