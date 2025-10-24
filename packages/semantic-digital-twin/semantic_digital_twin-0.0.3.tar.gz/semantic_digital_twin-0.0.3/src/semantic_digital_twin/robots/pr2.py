from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Self

from .robot_mixins import HasNeck, SpecifiesLeftRightArm
from ..datastructures.prefixed_name import PrefixedName
from ..robots.abstract_robot import (
    Neck,
    Finger,
    ParallelGripper,
    Arm,
    Camera,
    FieldOfView,
    Torso,
    AbstractRobot,
)
from ..spatial_types import Quaternion, Vector3
from ..world import World


@dataclass
class PR2(AbstractRobot, SpecifiesLeftRightArm, HasNeck):
    """
    Represents the Personal Robot 2 (PR2), which was originally created by Willow Garage.
    The PR2 robot consists of two arms, each with a parallel gripper, a head with a camera, and a prismatic torso
    """

    def __hash__(self):
        return hash(
            tuple(
                [self.__class__]
                + sorted([kse.name for kse in self.kinematic_structure_entities])
            )
        )

    def load_srdf(self):
        """
        Loads the SRDF file for the PR2 robot, if it exists.
        """
        srdf_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "resources",
            "collision_configs",
            "pr2.srdf",
        )
        self._world.load_collision_srdf(srdf_path)

    @classmethod
    def from_world(cls, world: World) -> Self:
        """
        Creates a PR2 robot view from the given world.

        :param world: The world from which to create the robot view.

        :return: A PR2 robot view.
        """

        robot = cls(
            name=PrefixedName(name="pr2", prefix=world.name),
            root=world.get_body_by_name("base_footprint"),
            _world=world,
        )

        # Create left arm
        left_gripper_thumb = Finger(
            name=PrefixedName("left_gripper_thumb", prefix=robot.name.name),
            root=world.get_body_by_name("l_gripper_l_finger_link"),
            tip=world.get_body_by_name("l_gripper_l_finger_tip_link"),
            _world=world,
        )

        left_gripper_finger = Finger(
            name=PrefixedName("left_gripper_finger", prefix=robot.name.name),
            root=world.get_body_by_name("l_gripper_r_finger_link"),
            tip=world.get_body_by_name("l_gripper_r_finger_tip_link"),
            _world=world,
        )

        left_gripper = ParallelGripper(
            name=PrefixedName("left_gripper", prefix=robot.name.name),
            root=world.get_body_by_name("l_gripper_palm_link"),
            tool_frame=world.get_body_by_name("l_gripper_tool_frame"),
            front_facing_orientation=Quaternion(0, 0, 0, 1),
            front_facing_axis=Vector3(1, 0, 0),
            thumb=left_gripper_thumb,
            finger=left_gripper_finger,
            _world=world,
        )
        left_arm = Arm(
            name=PrefixedName("left_arm", prefix=robot.name.name),
            root=world.get_body_by_name("torso_lift_link"),
            tip=world.get_body_by_name("l_wrist_roll_link"),
            manipulator=left_gripper,
            _world=world,
        )

        robot.add_arm(left_arm)

        # Create right arm
        right_gripper_thumb = Finger(
            name=PrefixedName("right_gripper_thumb", prefix=robot.name.name),
            root=world.get_body_by_name("r_gripper_l_finger_link"),
            tip=world.get_body_by_name("r_gripper_l_finger_tip_link"),
            _world=world,
        )
        right_gripper_finger = Finger(
            name=PrefixedName("right_gripper_finger", prefix=robot.name.name),
            root=world.get_body_by_name("r_gripper_r_finger_link"),
            tip=world.get_body_by_name("r_gripper_r_finger_tip_link"),
            _world=world,
        )
        right_gripper = ParallelGripper(
            name=PrefixedName("right_gripper", prefix=robot.name.name),
            root=world.get_body_by_name("r_gripper_palm_link"),
            tool_frame=world.get_body_by_name("r_gripper_tool_frame"),
            front_facing_orientation=Quaternion(0, 0, 0, 1),
            front_facing_axis=Vector3(1, 0, 0),
            thumb=right_gripper_thumb,
            finger=right_gripper_finger,
            _world=world,
        )
        right_arm = Arm(
            name=PrefixedName("right_arm", prefix=robot.name.name),
            root=world.get_body_by_name("torso_lift_link"),
            tip=world.get_body_by_name("r_wrist_roll_link"),
            manipulator=right_gripper,
            _world=world,
        )

        robot.add_arm(right_arm)

        # Create camera and neck
        camera = Camera(
            name=PrefixedName("wide_stereo_optical_frame", prefix=robot.name.name),
            root=world.get_body_by_name("wide_stereo_optical_frame"),
            forward_facing_axis=Vector3(0, 0, 1),
            field_of_view=FieldOfView(horizontal_angle=0.99483, vertical_angle=0.75049),
            minimal_height=1.27,
            maximal_height=1.60,
            _world=world,
        )

        neck = Neck(
            name=PrefixedName("neck", prefix=robot.name.name),
            sensors={camera},
            root=world.get_body_by_name("head_pan_link"),
            tip=world.get_body_by_name("head_tilt_link"),
            pitch_body=world.get_body_by_name("head_tilt_link"),
            yaw_body=world.get_body_by_name("head_pan_link"),
            _world=world,
        )
        robot.add_neck(neck)

        # Create torso
        torso = Torso(
            name=PrefixedName("torso", prefix=robot.name.name),
            root=world.get_body_by_name("torso_lift_link"),
            tip=world.get_body_by_name("torso_lift_link"),
            _world=world,
        )
        robot.add_torso(torso)

        world.add_semantic_annotation(robot, exists_ok=True)

        vel_limits = defaultdict(
            lambda: 1,
            {
                world.get_connection_by_name("head_tilt_joint"): 3.5,
                world.get_connection_by_name("r_shoulder_pan_joint"): 0.15,
                world.get_connection_by_name("l_shoulder_pan_joint"): 0.15,
                world.get_connection_by_name("r_shoulder_lift_joint"): 0.2,
                world.get_connection_by_name("l_shoulder_lift_joint"): 0.2,
            },
        )
        robot.tighten_dof_velocity_limits_of_1dof_connections(new_limits=vel_limits)

        return robot
