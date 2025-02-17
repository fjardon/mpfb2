"""This module provides and information holder for MHCLO files."""

import bpy, os, sys, json
from mathutils import Vector
from mpfb.services.objectservice import ObjectService
from mpfb.services.logservice import LogService
from mpfb.services.locationservice import LocationService

_LOG = LogService.get_logger("entities.mhclo")

_CONFIG_FILE = None

class Mhclo:
    """A representation of the values of a MHCLO file."""

    def __init__(self):
        """Create an empty MHCLO object with default values."""
        self.obj_file = None
        self.x_scale = None
        self.y_scale = None
        self.z_scale = None
        self.author = "unknown"
        self.license = "CC0"
        self.name = "imported_cloth"
        self.description = "no description"
        self.material = None
        self.tags = ""
        self.zdepth = 50
        self.first = 0
        self.verts = {}
        self.delverts = []
        self.delete = False
        self.delete_group = "Delete"
        self.uuid = None

    def load(self, mhclo_filename):
        """Populate settings from contents of a MHCLO file. This will not automatically load the
        mesh or the materials."""

        if not mhclo_filename:
            raise ValueError('Cannot load empty file name')

        if not os.path.exists(mhclo_filename):
            raise IOError(mhclo_filename + " does not exist")

        _LOG.debug("Will try to parse file", mhclo_filename)

        #realpath = os.path.realpath(os.path.expanduser(mhclo_filename))
        realpath = os.path.realpath(mhclo_filename)
        folder = os.path.dirname(realpath)

        try:
            fp = open(mhclo_filename, "r", encoding="utf8", errors="surrogateescape")
        except:
            _LOG.error("Error trying to open file:", sys.exc_info()[0])
            return None

        vn = 0
        status = ""

        for line in fp:
            words= line.split()
            _LOG.debug("Line", words)

            l = len(words)

            if l == 0:
                status = ""
                continue

            # at least grab what you get from the comment
            #
            if words[0] == '#':
                if l > 2:
                    key = words[1].lower()
                    if "author" in key:
                        self.author = words[2]
                    elif "license" in key:
                        if "by" in line.lower():
                            self.license = "CC-BY"
                        elif "apgl" in line.lower():
                            self.license = "AGPL"
                    elif "description" in key:
                        self.description = " ".join(words[2:])
                continue

            if words[0] == "material":
                self.material = os.path.join(folder, words[1])
                continue

            if str(words[0]).startswith("vertexboneweights"):
                # Workaround for fixing ancient system assets
                continue

            # read vertices lines
            #
            if status == 'v':
                if words[0].isnumeric() is False:
                    _LOG.debug("Breaking vertex listing loop on", words)
                    status = ""
                    continue
                if l == 1:
                    v = int(words[0])
                    self.verts[vn] = {'verts': (v,v,v), 'weights': (1,0,0), 'offsets': Vector((0,0,0))}
                else:
                    v0 = int(words[0])
                    v1 = int(words[1])
                    v2 = int(words[2])
                    w0 = float(words[3])
                    w1 = float(words[4])
                    w2 = float(words[5])
                    d0 = float(words[6])
                    d1 = float(words[7])
                    d2 = float(words[8])
                    self.verts[vn] = {'verts': (v0,v1,v2), 'weights': (w0,w1,w2), 'offsets': Vector((d0,-d2,d1))}
                vn += 1
                continue
            elif status == 'd':
                if words[0].isnumeric() is False:
                    status = ""
                    continue
                sequence = False
                for v in words:
                    if v == "-":
                        sequence = True
                    else:
                        v1 = int(v)
                        if sequence:
                            for vn in range(v0,v1+1):
                                self.delverts.append(vn)
                            sequence = False
                        else:
                            self.delverts.append(v1)
                        v0 = v1
                continue

            key = words[0]
            status = ""
            if key == 'obj_file':
                self.obj_file = os.path.join(folder, words[1])
                _LOG.debug("obj_file", self.obj_file)
            elif key == 'verts':
                if len(words) > 1:
                    self.first = int(words[1])      # this value will be ignored, we always start from zero
                    status = "v"
            elif key == 'x_scale':
                self.x_scale = (int(words[1]), int(words[2]), float(words[3]))
            elif key == 'y_scale':
                self.y_scale = (int(words[1]), int(words[2]), float(words[3]))
            elif key == 'z_scale':
                self.z_scale = (int(words[1]), int(words[2]), float(words[3]))
            elif key == 'name':
                self.name = words[1]
            elif key == 'z_depth':
                self.zdepth = int(words[1])
            elif key == 'uuid':
                self.uuid = words[1]
            elif key == 'tag':
                if self.tags != "":
                    self.tags += ","
                self.tags += words[1].lower()
            elif key == 'delete_verts':
                self.delete = True
                status = 'd'

        if not self.obj_file:
            _LOG.warn("Reaching end of mhclo parsing without finding obj file")

        fp.close

    def load_mesh(self, context):

        if self.obj_file == "" or not self.obj_file:
            raise ValueError('No obj file has been specified')

        _LOG.debug("Will try to load wavefront file", self.obj_file)
        obj = ObjectService.load_wavefront_file(self.obj_file, context)
        _LOG.debug("Loaded object:", obj)
        if obj is not None:
            self.clothes = obj
        else:
            raise IOError("Failed to load clothes mesh")
        return obj

    def _get_config_file(self):
        global _CONFIG_FILE
        if _CONFIG_FILE is None:
            metadata = LocationService.get_mpfb_data("mesh_metadata")
            config_file = os.path.join(metadata, "hm08_config.json")
            with open(config_file, 'r') as json_file:
                _CONFIG_FILE = json.load(json_file)
        return _CONFIG_FILE

    def set_scalings (self, context, human):
        mesh_config = self._get_config_file()
        for bodypart in mesh_config["dimensions"]:
            dims = mesh_config["dimensions"][bodypart]
            #
            # I think it is okay to check only one dimension to figure out on
            # what the piece of cloth was created
            #
            if self.x_scale and dims['xmin'] == self.x_scale[0] and dims['xmax'] == self.x_scale[1]:
                pass
                # TODO: Need to update with new names for makeclothes properties
                #context.active_object.MhOffsetScale = bodypart
        return
