"""This module provides functionality for converting a rig to rigify.

The code is based on an approach suggested by Andrea Rossato in https://www.youtube.com/watch?v=zmsuLD7hAUA
"""

import bpy

from mpfb.services.logservice import LogService
from mpfb.services.objectservice import ObjectService
_LOG = LogService.get_logger("rigifyhelpers.rigifyhelpers")

from mpfb.services.rigservice import RigService

class RigifyHelpers():

    """This is the abstract rig type independent base class for working with
    rigify. You will want to call the static get_instance() method to get a
    concrete implementation for the specific rig you are working with."""

    def __init__(self, settings):
        """Get a new instance of RigifyHelpers. You should not call this directly.
        Use get_instance() instead."""

        _LOG.debug("Constructing RigifyHelpers object")
        self.settings = settings
        _LOG.dump("settings", self.settings)
        self.produce = "produce" in settings and settings["produce"]
        self.keep_meta = "keep_meta" in settings and settings["keep_meta"]

    @staticmethod
    def get_instance(settings, rigtype="Default"):
        """Get an implementation instance matching the rig type."""

        _LOG.enter()
        from mpfb.services.rigifyhelpers.gameenginerigifyhelpers import GameEngineRigifyHelpers  # pylint: disable=C0415
        return GameEngineRigifyHelpers(settings)

    def convert_to_rigify(self, armature_object):
        _LOG.enter()

        self._setup_spine(armature_object)
        self._setup_arms(armature_object)
        self._setup_legs(armature_object)
        self._setup_shoulders(armature_object)
        self._setup_head(armature_object)
        self._setup_fingers(armature_object)

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        name = armature_object.name

        if "name" in self.settings:
            name = str(self.settings["name"]).strip()

        if name:
            target_name = name
            if ObjectService.object_name_exists("RIG-" + name):
                target_name = ObjectService.ensure_unique_name("RIG-" + name)
                target_name = target_name.replace("RIG-", "")
            if hasattr(armature_object.data, 'rigify_rig_basename'):
                armature_object.data.rigify_rig_basename = target_name
            else:
                armature_object.name = target_name

        if self.produce:
            bpy.ops.pose.rigify_generate()

            rigify_object = bpy.context.active_object
            rigify_object.show_in_front = True

            child_meshes = ObjectService.get_list_of_children(armature_object)
            for child_mesh in child_meshes:
                self._adjust_mesh_for_rigify(child_mesh, rigify_object)

            if not self.keep_meta:
                bpy.data.objects.remove(armature_object, do_unlink=True)

    def _adjust_mesh_for_rigify(self, child_mesh, rigify_object):
        all_relevant_bones = []
        all_relevant_bones.extend(self.get_list_of_spine_bones())
        all_relevant_bones.extend(self.get_list_of_head_bones())
        for side in [True, False]:
            all_relevant_bones.extend(self.get_list_of_leg_bones(side))
            all_relevant_bones.extend(self.get_list_of_arm_bones(side))
            all_relevant_bones.extend(self.get_list_of_shoulder_bones(side))
            for i in range(5):
                all_relevant_bones.extend(self.get_list_of_finger_bones(i, side))

        for bone_name in all_relevant_bones:
            if bone_name in child_mesh.vertex_groups:
                vertex_group = child_mesh.vertex_groups.get(bone_name)
                _LOG.debug("Renaming vertex group", (child_mesh.name, vertex_group.name, "DEF-" + vertex_group.name))
                vertex_group.name = "DEF-" + vertex_group.name

        for modifier in child_mesh.modifiers:
            if isinstance(modifier, bpy.types.ArmatureModifier):
                modifier.object = rigify_object

        child_mesh.parent = rigify_object

    def _set_use_connect_on_bones(self, armature_object, bone_names, exclude_first=True):
        _LOG.enter()
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        if exclude_first:
            bone_names = list(bone_names) # to modify a copy rather than the source list
            bone_names.pop(0)

        for bone_name in bone_names:
            _LOG.debug("About to set use_connect on", bone_name)
            edit_bone = RigService.find_edit_bone_by_name(bone_name, armature_object)
            edit_bone.use_connect = True
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    def _setup_spine(self, armature_object):
        _LOG.enter()
        spine = self.get_list_of_spine_bones() # pylint: disable=E1111
        _LOG.dump("Spine", spine)
        self._set_use_connect_on_bones(armature_object, spine)
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        first_spine_bone = RigService.find_pose_bone_by_name(spine[0], armature_object)
        first_spine_bone.rigify_type = 'spines.basic_spine'
        first_spine_bone.rigify_parameters.segments = len(spine)
        # TODO: change layers

    def _setup_arms(self, armature_object):
        _LOG.enter()
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        for side in [True, False]:
            arm = self.get_list_of_arm_bones(side) # pylint: disable=E1111
            _LOG.dump("Arm", arm)
            self._set_use_connect_on_bones(armature_object, arm)
            first_arm_bone = RigService.find_pose_bone_by_name(arm[0], armature_object)
            first_arm_bone.rigify_type = 'limbs.arm'
            #first_arm_bone.rigify_parameters.segments = len(arm)
        # TODO: change layers

    def _setup_legs(self, armature_object):
        _LOG.enter()
        for side in [True, False]:
            leg = self.get_list_of_leg_bones(side) # pylint: disable=E1111
            _LOG.dump("Leg", leg)
            self._set_use_connect_on_bones(armature_object, leg)
            bpy.ops.object.mode_set(mode='POSE', toggle=False)

            toe_bone_name = leg[-1]
            toe = RigService.find_pose_bone_by_name(toe_bone_name, armature_object)
            toe_bone_head = toe.head
            toe_bone_length = toe.length
            _LOG.debug("Toe bone", (toe_bone_name, toe_bone_head, toe_bone_length))

            foot_bone_name = self.get_foot_name(side)
            _LOG.debug("Foot bone name", foot_bone_name)
            foot = RigService.find_pose_bone_by_name(foot_bone_name, armature_object)
            foot_bone_head = foot.head
            foot_bone_length = foot.length
            _LOG.debug("Foot bone data", (foot_bone_head, foot_bone_length))

            first_leg_bone = RigService.find_pose_bone_by_name(leg[0], armature_object)
            first_leg_bone.rigify_type = 'limbs.leg'

            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

            bone_side = 'R'
            if side:
                bone_side = 'L'

            bones = armature_object.data.edit_bones
            bone = bones.new("heel.02." + bone_side)

            head = [toe_bone_head[0], foot_bone_head[1], toe_bone_head[2]]
            tail = [toe_bone_head[0], foot_bone_head[1], toe_bone_head[2]]
            if side:
                head[0] = head[0] - toe_bone_length / 2
                tail[0] = tail[0] + toe_bone_length / 2
            else:
                head[0] = head[0] + toe_bone_length / 2
                tail[0] = tail[0] - toe_bone_length / 2

            bone.head = head
            bone.tail = tail

            foot = RigService.find_edit_bone_by_name(foot_bone_name, armature_object)
            bone.parent = foot

            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            bpy.ops.object.mode_set(mode='POSE', toggle=False)


    def _setup_shoulders(self, armature_object):
        _LOG.enter()
        for side in [True, False]:
            shoulder = self.get_list_of_shoulder_bones(side) # pylint: disable=E1111
            _LOG.dump("Shoulder", shoulder)
            self._set_use_connect_on_bones(armature_object, shoulder)
            bpy.ops.object.mode_set(mode='POSE', toggle=False)
            first_shoulder_bone = RigService.find_pose_bone_by_name(shoulder[0], armature_object)
            first_shoulder_bone.rigify_type = 'basic.super_copy'

    def _setup_head(self, armature_object):
        _LOG.enter()
        head = self.get_list_of_head_bones() # pylint: disable=E1111
        _LOG.dump("Head", head)
        self._set_use_connect_on_bones(armature_object, head)
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        first_head_bone = RigService.find_pose_bone_by_name(head[0], armature_object)
        first_head_bone.rigify_type = 'spines.super_head'

    def _setup_fingers(self, armature_object):
        _LOG.enter()
        for side in [True, False]:
            for finger_number in range(5):
                finger = self.get_list_of_finger_bones(finger_number, side) # pylint: disable=E1111
                _LOG.dump("Finger", finger)
                self._set_use_connect_on_bones(armature_object, finger)
                bpy.ops.object.mode_set(mode='POSE', toggle=False)
                first_finger_bone = RigService.find_pose_bone_by_name(finger[0], armature_object)
                first_finger_bone.rigify_type = 'limbs.super_finger'

    def get_foot_name(self, left_side=True):
        """Abstract method for getting the name of a foot bone, must be overriden by rig specific implementation classes."""
        _LOG.enter()
        raise NotImplementedError("the get_foot_name() method must be overriden by the rig class")

    def get_list_of_spine_bones(self):
        """Abstract method for getting a list of bones in the spine, must be overriden by rig specific implementation classes."""
        _LOG.enter()
        raise NotImplementedError("the get_list_of_spine_bones() method must be overriden by the rig class")

    def get_list_of_arm_bones(self, left_side=True):
        """Abstract method for getting a list of bones in an arm, must be overriden by rig specific implementation classes."""
        _LOG.enter()
        raise NotImplementedError("the get_list_of_arm_bones() method must be overriden by the rig class")

    def get_list_of_leg_bones(self, left_side=True):
        """Abstract method for getting a list of bones in a leg, must be overriden by rig specific implementation classes."""
        _LOG.enter()
        raise NotImplementedError("the get_list_of_leg_bones() method must be overriden by the rig class")

    def get_list_of_shoulder_bones(self, left_side=True):
        """Abstract method for getting a list of bones in a shoulder, must be overriden by rig specific implementation classes."""
        _LOG.enter()
        raise NotImplementedError("the get_list_of_shoulder_bones() method must be overriden by the rig class")

    def get_list_of_head_bones(self):
        """Abstract method for getting a list of bones in the head, must be overriden by rig specific implementation classes."""
        _LOG.enter()
        raise NotImplementedError("the get_list_of_head_bones() method must be overriden by the rig class")

    def get_list_of_finger_bones(self, finger_number, left_side=True):
        """Abstract method for getting a list of bones in a finger, must be overriden by rig specific implementation classes."""
        _LOG.enter()
        raise NotImplementedError("the get_list_of_finger_bones() method must be overriden by the rig class")
