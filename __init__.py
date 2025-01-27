from . import blender_panels
from . import pmo_export_menu
from . import skel_io
from . import pac_export_menu


bl_info = {
    "name": "PMO Export",
    "blender": (2, 80, 0),
    "category": "Import-Export",
}


def register():
    blender_panels.register()
    pmo_export_menu.register()
    skel_io.register()
    pac_export_menu.register()


def unregister():
    blender_panels.unregister()
    pmo_export_menu.unregister()
    skel_io.unregister()
    pac_export_menu.unregister()

if __name__ == "__main__":
    register()
