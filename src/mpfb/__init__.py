"""This is the MakeHuman Plugin For Blender (MPFB). For more information, see
the README.md file in the zip."""

bl_info = { # pylint: disable=C0103
    "name": "mpfb",
    "author": "Joel Palmius",
    "version": (1, 9, 9),
    "blender": (2, 90, 0),
    "warning": "Plugin is in Alpha stage",
    "location": "View3D > Properties > MH",
    "description": "MakeHuman Plugin For Blender",
    "wiki_url": "https://github.com/makehumancommunity/makehuman-plugin-for-blender",
    "category": "MakeHuman"}

# These are constants that can be imported from submodules
VERSION = bl_info["version"]

# Don't import this log object. Instead, get a local logger via LogService
_LOG = None

# WARNING!!!
# Do not try to import anything from anywhere outside of the register method.
# We can only rely on singletons in the rest of the module being initialized
# and available once blender has gotten far enough as to call register.
#
# Because of this we will also disable pylint's warning about these imports
# pylint: disable=C0415
#
# We will also disable warnings about unused imports, since the point of
# importing here is to just make sure everything is up and running
# pylint: disable=W0611

from ._classmanager import ClassManager
import bpy
from bpy.utils import register_class

def get_preference(name):
    _LOG.enter()
    if "mpfb" in bpy.context.preferences.addons:
        mpfb = bpy.context.preferences.addons['mpfb']
        if hasattr(mpfb, "preferences"):
            prefs = mpfb.preferences
            if hasattr(prefs, name):
                value = getattr(prefs, name)
                _LOG.debug("Found addon preference", (name, value))
                return value
            _LOG.error("There were addon preferences, but key did not exist:", name)
            _LOG.error("preferences", dir(prefs))
            _LOG.error("hasattr", hasattr(prefs, name))
            _LOG.error("name in", name in prefs)
            return None
        _LOG.crash("The 'mpfb' addon does not have any preferences")
        raise ValueError("Preferences have not been initialized properly")
    _LOG.crash("The 'mpfb' addon does not exist!?")
    raise ValueError("I don't seem to exist")

def register():
    """At this point blender is ready enough for it to make sense to
    start initializing python singletons"""

    # Preferences will be needed before starting the rest of the addon
    from ._preferences import MpfbPreferences
    try:
        register_class(MpfbPreferences)
    except:
        print("WARNING: Could not register preferences class. Maybe it was registered by an earlier version of MPFB?")

    global _LOG # pylint: disable=W0603

    from mpfb.services.logservice import LogService
    _LOG = LogService.get_logger("mpfb.init")
    _LOG.reset_timer()
    _LOG.debug("We're in register() and about to start registering classes.")

    # ClassManager is a singleton to which all modules can add their
    # Blender classes, preferably when the module is imported the first
    # time. Thus we'll import all packages which can theoretically
    # contain blender classes.

    if not ClassManager.isinitialized():
        classmanager = ClassManager() # pylint: disable=W0612

    _LOG.debug("About to import mpfb.services")
    import mpfb.services.locationservice
    import mpfb.services.socketservice
    import mpfb.services.uiservice

    _LOG.debug("About to import mpfb.ui")
    import mpfb.ui

    _LOG.debug("After imports")

    # We can now assume all relevant classes have been added to the
    # class manager singleton.

    _LOG.debug("About to request class registration")
    ClassManager.register_classes()

    _LOG.debug("About to check if MakeHuman is online")

    # Try to fetch some basic information (doesn't really matter which) from
    # makehuman to see if it responds at all.

    from mpfb.services.socketservice import SocketService

    mh_user_dir = None
    try:
        mh_user_dir = SocketService.get_user_dir()
        _LOG.info("MakeHuman user dir is", mh_user_dir)
    except ConnectionRefusedError as err:
        _LOG.error("Could not read mh_user_dir. Maybe socket server is down? Error was:", err)
        mh_user_dir = None

    mh_sys_dir = None
    try:
        mh_sys_dir = SocketService.get_sys_dir()
        _LOG.info("MakeHuman sys dir is", mh_sys_dir)
    except ConnectionRefusedError as err:
        _LOG.error("Could not read mh_sys_dir. Maybe socket server is down? Error was:", err)
        mh_sys_dir = None

    _LOG.time("Number of milliseconds to run entire register() method:")
    _LOG.info("MPFB initialization has finished.")


def unregister():
    """Deconstruct all loaded blenderish classes"""

    global _LOG # pylint: disable=W0603

    _LOG.debug("About to unregister classes")
    ClassManager.unregister_classes()


__all__ = ["VERSION"]
