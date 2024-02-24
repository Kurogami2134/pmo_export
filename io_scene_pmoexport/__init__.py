from io_scene_pmoexport import blender_panels
from io_scene_pmoexport import pmo_export_menu

bl_info = {
    "name": "PMO Export",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}


def register():
    blender_panels.register()
    pmo_export_menu.register()


def unregister():
    blender_panels.unregister()
    pmo_export_menu.unregister()


if __name__ == "__main__":
    register()
