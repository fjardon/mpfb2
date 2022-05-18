import os, bpy
from mpfb._classmanager import ClassManager
from mpfb.services.logservice import LogService
from mpfb.services.locationservice import LocationService
from mpfb.services.sceneconfigset import SceneConfigSet
from mpfb.services.uiservice import UiService
from mpfb.services.rigservice import RigService
from mpfb.ui.abstractpanel import Abstract_Panel

_LOG = LogService.get_logger("sculpt.sculptpanel")

_LOC = os.path.dirname(__file__)
SCULPT_PROPERTIES_DIR = os.path.join(_LOC, "properties")
SCULPT_PROPERTIES = SceneConfigSet.from_definitions_in_json_directory(SCULPT_PROPERTIES_DIR, prefix="SCL_")

class MPFB_PT_SculptPanel(Abstract_Panel):
    bl_label = "Set up for sculpt"
    bl_category = UiService.get_value("OPERATIONSCATEGORY")
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = "MPFB_PT_Operations_Panel"

    def draw(self, context):
        _LOG.enter()

        layout = self.layout
        scene = context.scene

        if context.object is None:
            return

        from mpfb.entities.objectproperties import GeneralObjectProperties

        objtype = GeneralObjectProperties.get_value("object_type", entity_reference=context.object)

        if not objtype or objtype == "Skeleton":
            return

        SCULPT_PROPERTIES.draw_properties(scene, layout, ["sculpt_strategy"])

        strategy = SCULPT_PROPERTIES.get_value("sculpt_strategy", entity_reference=scene)

        if not strategy:
            return

        SCULPT_PROPERTIES.draw_properties(scene, layout, ["setup_multires"])

        multires = SCULPT_PROPERTIES.get_value("setup_multires", entity_reference=scene)

        props = []

        if multires:
            props.append("multires_first")

        if objtype == "Basemesh":
            props.append("delete_helpers")

        if objtype in ["Basemesh", "Proxymeshes"]:
            props.append("remove_delete")

        props.append("apply_armature")

        if strategy in ["SOURCEDESTCOPY", "DESTCOPY"]:
            props.append("normal_material")
            material = SCULPT_PROPERTIES.get_value("normal_material", entity_reference=scene)
            if material:
                props.append("resolution")
            props.append("adjust_settings")

        if strategy == "SOURCEDESTCOPY":
            props.append("delete_origin")

        props.append("enter_sculpt")

        SCULPT_PROPERTIES.draw_properties(scene, layout, props)
        layout.operator("mpfb.setup_sculpt")


ClassManager.add_class(MPFB_PT_SculptPanel)
