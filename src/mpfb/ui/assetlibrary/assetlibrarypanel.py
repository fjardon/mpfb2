"""Asset library subpanels"""

import bpy
from mpfb import ClassManager
from mpfb.services.logservice import LogService
from mpfb.services.assetservice import AssetService, ASSET_LIBRARY_SECTIONS
from mpfb.ui.assetlibrary.assetsettingspanel import ASSET_SETTINGS_PROPERTIES
from mpfb.ui.assetspanel import FILTER_PROPERTIES

_LOG = LogService.get_logger("assetlibrary.assetlibrarypanel")

_NOASSETS = [
    "No assets in this section.",
    "Maybe set MH user data preference",
    "or install assets in MPFB user data"
    ]


class _Abstract_Asset_Library_Panel(bpy.types.Panel):
    """Asset library panel."""

    bl_label = "SHOULD BE OVERRIDDEN"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "MPFB_PT_Assets_Panel"
    bl_options = {'DEFAULT_CLOSED'}

    asset_subdir = "-"
    asset_type = "mhclo"
    skin_overrides = False
    eye_overrides = False
    object_type = "Clothes"

    def _draw_section(self, scene, layout):
        _LOG.enter()
        items = AssetService.get_asset_list(self.asset_subdir, self.asset_type)
        allnames = list(items.keys())
        if len(allnames) < 1:
            for line in _NOASSETS:
                layout.label(text=line)
            return
        allnames.sort()

        filter_term = str(FILTER_PROPERTIES.get_value("filter", entity_reference=scene)).strip().lower()

        names = []
        for name in allnames:
            if not filter_term:
                names.append(name)
            else:
                if filter_term in str(name).lower():
                    names.append(name)

        for name in names:
            box = layout.box()
            box.label(text=name)
            asset = items[name]
            _LOG.debug("Asset", asset)
            if "thumb" in asset and not asset["thumb"] is None:
                box.template_icon(icon_value=asset["thumb"].icon_id, scale=6.0)
            operator = None
            if self.asset_type == "mhclo":
                operator = box.operator("mpfb.load_library_clothes")
            if self.asset_type == "proxy":
                operator = box.operator("mpfb.load_library_proxy")
            if self.asset_type == "mhmat":
                if self.skin_overrides:
                    operator = box.operator("mpfb.load_library_skin")
            if not operator is None:
                operator.filepath = asset["full_path"]
                if hasattr(operator, "object_type") and self.object_type:
                    operator.object_type = self.object_type
                if hasattr(operator, "material_type"):
                    procedural_eyes = ASSET_SETTINGS_PROPERTIES.get_value("procedural_eyes", entity_reference=scene)
                    _LOG.debug("Eye settings, eye_overrides, procedural_eyes", (self.eye_overrides, procedural_eyes))
                    if self.eye_overrides and procedural_eyes:
                        operator.material_type = "PROCEDURAL_EYES"
                    else:
                        operator.material_type = "MAKESKIN"
                    _LOG.debug("Operator material type is now", operator.material_type)
                else:
                    _LOG.debug("Operator does not have a material type")


    def draw(self, context):
        _LOG.enter()
        layout = self.layout
        scene = context.scene

#===============================================================================
#         if not context.object:
#             return
#
#         if not ObjectService.object_is_basemesh(context.object):
#             return
#
#         basemesh = context.object
#===============================================================================

        self._draw_section(scene, layout)


for _definition in ASSET_LIBRARY_SECTIONS:
    _LOG.dump("Definition", _definition)
    _sub_panel = type("MPFB_PT_Asset_Library_Panel_" + _definition["asset_subdir"], (_Abstract_Asset_Library_Panel,), _definition)
    _LOG.debug("sub_panel", _sub_panel)
    ClassManager.add_class(_sub_panel)
