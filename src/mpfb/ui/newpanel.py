from mpfb._classmanager import ClassManager
from mpfb.services.logservice import LogService
from mpfb.services.uiservice import UiService
from mpfb.ui.abstractpanel import Abstract_Panel

_LOG = LogService.get_logger("ui.newpanel")

class MPFB_PT_New_Panel(Abstract_Panel):
    bl_label = "New human"
    bl_category = UiService.get_value("MODELCATEGORY")

    def draw(self, context):
        _LOG.enter()
        layout = self.layout
        scn = context.scene

ClassManager.add_class(MPFB_PT_New_Panel)
