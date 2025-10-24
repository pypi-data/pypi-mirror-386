import os
from collections import defaultdict

from typing_extensions import List

import numpy as np
import pytest
from rustworkx import NoPathFound

from semantic_digital_twin.reasoning.predicates import LeftOf
from semantic_digital_twin.robots.hsrb import HSRB
from semantic_digital_twin.spatial_types.spatial_types import TransformationMatrix
from semantic_digital_twin.world_description.connections import (
    OmniDrive,
    PrismaticConnection,
    RevoluteConnection,
)
from semantic_digital_twin.spatial_computations.ik_solver import (
    MaxIterationsException,
    UnreachableException,
)
from semantic_digital_twin.datastructures.prefixed_name import PrefixedName
from semantic_digital_twin.robots.abstract_robot import KinematicChain
from semantic_digital_twin.robots.tracy import Tracy
from semantic_digital_twin.robots.pr2 import PR2
from semantic_digital_twin.spatial_types.derivatives import Derivatives
from semantic_digital_twin.spatial_types.symbol_manager import symbol_manager
from semantic_digital_twin.world import World
from semantic_digital_twin.testing import pr2_world, tracy_world, hsrb_world


def test_compute_chain_of_bodies_pr2(pr2_world):
    root_link = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("base_footprint")
    )
    tip_link = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("r_gripper_tool_frame")
    )
    real = pr2_world.compute_chain_of_kinematic_structure_entities(
        root=root_link, tip=tip_link
    )
    real = [x.name for x in real]
    assert real == [
        PrefixedName(name="base_footprint", prefix="pr2"),
        PrefixedName(name="base_link", prefix="pr2"),
        PrefixedName(name="torso_lift_link", prefix="pr2"),
        PrefixedName(name="r_shoulder_pan_link", prefix="pr2"),
        PrefixedName(name="r_shoulder_lift_link", prefix="pr2"),
        PrefixedName(name="r_upper_arm_roll_link", prefix="pr2"),
        PrefixedName(name="r_upper_arm_link", prefix="pr2"),
        PrefixedName(name="r_elbow_flex_link", prefix="pr2"),
        PrefixedName(name="r_forearm_roll_link", prefix="pr2"),
        PrefixedName(name="r_forearm_link", prefix="pr2"),
        PrefixedName(name="r_wrist_flex_link", prefix="pr2"),
        PrefixedName(name="r_wrist_roll_link", prefix="pr2"),
        PrefixedName(name="r_gripper_palm_link", prefix="pr2"),
        PrefixedName(name="r_gripper_tool_frame", prefix="pr2"),
    ]


def test_compute_chain_of_connections_pr2(pr2_world):
    root_link = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("base_footprint")
    )
    tip_link = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("r_gripper_tool_frame")
    )
    real = pr2_world.compute_chain_of_connections(root=root_link, tip=tip_link)
    real = [x.name for x in real]
    assert real == [
        PrefixedName(name="base_footprint_joint", prefix="pr2"),
        PrefixedName(name="torso_lift_joint", prefix="pr2"),
        PrefixedName(name="r_shoulder_pan_joint", prefix="pr2"),
        PrefixedName(name="r_shoulder_lift_joint", prefix="pr2"),
        PrefixedName(name="r_upper_arm_roll_joint", prefix="pr2"),
        PrefixedName(name="r_upper_arm_joint", prefix="pr2"),
        PrefixedName(name="r_elbow_flex_joint", prefix="pr2"),
        PrefixedName(name="r_forearm_roll_joint", prefix="pr2"),
        PrefixedName(name="r_forearm_joint", prefix="pr2"),
        PrefixedName(name="r_wrist_flex_joint", prefix="pr2"),
        PrefixedName(name="r_wrist_roll_joint", prefix="pr2"),
        PrefixedName(name="r_gripper_palm_joint", prefix="pr2"),
        PrefixedName(name="r_gripper_tool_joint", prefix="pr2"),
    ]


def test_compute_chain_of_bodies_error_pr2(pr2_world):
    root = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("r_gripper_tool_frame")
    )
    tip = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("base_footprint")
    )
    with pytest.raises(NoPathFound):
        pr2_world.compute_chain_of_kinematic_structure_entities(root, tip)


def test_compute_chain_of_connections_error_pr2(pr2_world):
    root = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("r_gripper_tool_frame")
    )
    tip = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("base_footprint")
    )
    with pytest.raises(NoPathFound):
        pr2_world.compute_chain_of_connections(root, tip)


def test_compute_split_chain_of_bodies_pr2(pr2_world):
    root = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("l_gripper_r_finger_tip_link")
    )
    tip = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("l_gripper_l_finger_tip_link")
    )
    chain1, connection, chain2 = (
        pr2_world.compute_split_chain_of_kinematic_structure_entities(root, tip)
    )
    chain1 = [n.name.name for n in chain1]
    connection = [n.name.name for n in connection]
    chain2 = [n.name.name for n in chain2]
    assert chain1 == [
        "l_gripper_r_finger_tip_link",
        "l_gripper_r_finger_link",
    ]
    assert connection == ["l_gripper_palm_link"]
    assert chain2 == ["l_gripper_l_finger_link", "l_gripper_l_finger_tip_link"]


def test_get_split_chain_pr2(pr2_world):
    root = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("l_gripper_r_finger_tip_link")
    )
    tip = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("l_gripper_l_finger_tip_link")
    )
    chain1, chain2 = pr2_world.compute_split_chain_of_connections(root, tip)
    chain1 = [n.name.name for n in chain1]
    chain2 = [n.name.name for n in chain2]
    assert chain1 == ["l_gripper_r_finger_tip_joint", "l_gripper_r_finger_joint"]
    assert chain2 == ["l_gripper_l_finger_joint", "l_gripper_l_finger_tip_joint"]


def test_compute_fk_np_pr2(pr2_world):
    tip = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("r_gripper_tool_frame")
    )
    root = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("l_gripper_tool_frame")
    )
    fk = pr2_world.compute_forward_kinematics_np(root, tip)
    np.testing.assert_array_almost_equal(
        fk,
        np.array(
            [
                [1.0, 0.0, 0.0, -0.0356],
                [0, 1.0, 0.0, -0.376],
                [0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )


def test_compute_fk_np_l_elbow_flex_joint_pr2(pr2_world):
    tip = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("l_elbow_flex_link")
    )
    root = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("l_upper_arm_link")
    )

    fk_expr = pr2_world.compose_forward_kinematics_expression(root, tip)
    fk_expr_compiled = fk_expr.compile()
    fk2 = fk_expr_compiled(
        symbol_manager.resolve_symbols(*fk_expr_compiled.symbol_parameters)
    )

    np.testing.assert_array_almost_equal(
        fk2,
        np.array(
            [
                [0.988771, 0.0, -0.149438, 0.4],
                [0.0, 1.0, 0.0, 0.0],
                [0.149438, 0.0, 0.988771, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )


def test_compute_ik(pr2_world):
    bf = pr2_world.root
    eef = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("r_gripper_tool_frame")
    )
    fk = pr2_world.compute_forward_kinematics_np(bf, eef)
    fk[0, 3] -= 0.2
    joint_state = pr2_world.compute_inverse_kinematics(
        bf, eef, TransformationMatrix(fk, reference_frame=bf)
    )
    for joint, state in joint_state.items():
        pr2_world.state[joint.name].position = state
    pr2_world.notify_state_change()
    actual_fk = pr2_world.compute_forward_kinematics_np(bf, eef)
    assert np.allclose(actual_fk, fk, atol=1e-3)


def test_compute_ik_max_iter(pr2_world):
    bf = pr2_world.root
    eef = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("r_gripper_tool_frame")
    )
    fk = pr2_world.compute_forward_kinematics_np(bf, eef)
    fk[2, 3] = 10
    with pytest.raises(MaxIterationsException):
        pr2_world.compute_inverse_kinematics(
            bf, eef, TransformationMatrix(fk, reference_frame=bf)
        )


def test_compute_ik_unreachable(pr2_world):
    bf = pr2_world.root
    eef = pr2_world.get_kinematic_structure_entity_by_name(
        PrefixedName("base_footprint")
    )
    fk = pr2_world.compute_forward_kinematics_np(bf, eef)
    fk[2, 3] = -1
    with pytest.raises(UnreachableException):
        pr2_world.compute_inverse_kinematics(
            bf, eef, TransformationMatrix(fk, reference_frame=bf)
        )


def test_apply_control_commands_omni_drive_pr2(pr2_world):
    omni_drive: OmniDrive = pr2_world.get_connection_by_name(
        PrefixedName("odom_combined_T_base_footprint")
    )
    cmd = np.zeros((len(pr2_world.degrees_of_freedom)), dtype=float)
    cmd[pr2_world.state._index[omni_drive.x_vel.name]] = 100
    cmd[pr2_world.state._index[omni_drive.y_vel.name]] = 100
    cmd[pr2_world.state._index[omni_drive.yaw.name]] = 100
    dt = 0.1
    pr2_world.apply_control_commands(cmd, dt, Derivatives.jerk)
    assert pr2_world.state[omni_drive.yaw.name].jerk == 100.0
    assert pr2_world.state[omni_drive.yaw.name].acceleration == 100.0 * dt
    assert pr2_world.state[omni_drive.yaw.name].velocity == 100.0 * dt * dt
    assert pr2_world.state[omni_drive.yaw.name].position == 100.0 * dt * dt * dt

    assert pr2_world.state[omni_drive.x_vel.name].jerk == 100.0
    assert pr2_world.state[omni_drive.x_vel.name].acceleration == 100.0 * dt
    assert pr2_world.state[omni_drive.x_vel.name].velocity == 100.0 * dt * dt
    assert pr2_world.state[omni_drive.x_vel.name].position == 0

    assert pr2_world.state[omni_drive.y_vel.name].jerk == 100.0
    assert pr2_world.state[omni_drive.y_vel.name].acceleration == 100.0 * dt
    assert pr2_world.state[omni_drive.y_vel.name].velocity == 100.0 * dt * dt
    assert pr2_world.state[omni_drive.y_vel.name].position == 0

    assert pr2_world.state[omni_drive.x.name].jerk == 0.0
    assert pr2_world.state[omni_drive.x.name].acceleration == 0.0
    assert pr2_world.state[omni_drive.x.name].velocity == 0.0
    assert pr2_world.state[omni_drive.x.name].position == 0.08951707486311977

    assert pr2_world.state[omni_drive.y.name].jerk == 0.0
    assert pr2_world.state[omni_drive.y.name].acceleration == 0.0
    assert pr2_world.state[omni_drive.y.name].velocity == 0.0
    assert pr2_world.state[omni_drive.y.name].position == 0.1094837581924854


def test_search_for_connections_of_type(pr2_world: World):
    connections = pr2_world.get_connections_by_type(OmniDrive)
    assert len(connections) == 1
    assert connections[0].name == PrefixedName(
        name="odom_combined_T_base_footprint", prefix="pr2"
    )
    assert connections[0].parent == pr2_world.root
    assert connections[0].child == pr2_world.get_kinematic_structure_entity_by_name(
        "base_footprint"
    )

    connections = pr2_world.get_connections_by_type(PrismaticConnection)
    assert len(connections) == 3
    assert connections[0].name == PrefixedName(name="torso_lift_joint", prefix="pr2")
    assert connections[0].parent == pr2_world.get_kinematic_structure_entity_by_name(
        "base_link"
    )
    assert connections[0].child == pr2_world.get_kinematic_structure_entity_by_name(
        "torso_lift_link"
    )
    assert connections[1].name == PrefixedName(
        name="r_gripper_motor_slider_joint", prefix="pr2"
    )
    assert connections[1].parent == pr2_world.get_kinematic_structure_entity_by_name(
        "r_gripper_palm_link"
    )
    assert connections[1].child == pr2_world.get_kinematic_structure_entity_by_name(
        "r_gripper_motor_slider_link"
    )
    assert connections[2].name == PrefixedName(
        name="l_gripper_motor_slider_joint", prefix="pr2"
    )
    assert connections[2].parent == pr2_world.get_kinematic_structure_entity_by_name(
        "l_gripper_palm_link"
    )
    assert connections[2].child == pr2_world.get_kinematic_structure_entity_by_name(
        "l_gripper_motor_slider_link"
    )

    connections = pr2_world.get_connections_by_type(RevoluteConnection)
    assert len(connections) == 40


def test_pr2_semantic_annotation(pr2_world):
    pr2 = PR2.from_world(pr2_world)

    # Ensure there are no loose bodies
    pr2_world._notify_model_change()

    assert len(pr2.manipulators) == 2
    assert len(pr2.manipulator_chains) == 2
    assert len(pr2.sensors) == 1
    assert len(pr2.sensor_chains) == 1
    assert pr2.neck == list(pr2.sensor_chains)[0]
    assert pr2.torso.name.name == "torso"
    assert len(pr2.torso.sensors) == 0
    assert list(pr2.sensor_chains)[0].sensors == pr2.sensors
    assert pr2.left_arm and pr2.right_arm
    assert pr2.left_arm != pr2.right_arm


def test_specifies_left_right_arm_mixin(pr2_world):
    pr2 = PR2.from_world(pr2_world)
    left_arm_chain = list(pr2.left_arm.bodies)
    right_arm_chain = list(pr2.right_arm.bodies)
    assert LeftOf(
        left_arm_chain[1],
        right_arm_chain[1],
        pr2.root.global_pose,
    )()


def test_kinematic_chains(pr2_world):
    pr2 = PR2.from_world(pr2_world)
    semantic_kinematic_chain_annotation: List[KinematicChain] = (
        pr2_world.get_semantic_annotations_by_type(KinematicChain)
    )
    for chain in semantic_kinematic_chain_annotation:
        assert chain.root
        assert chain.tip


def test_load_collision_config_srdf(pr2_world):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "resources",
        "collision_configs",
        "pr2.srdf",
    )
    pr2_world.load_collision_srdf(path)
    assert len([b for b in pr2_world.bodies if b.get_collision_config().disabled]) == 20
    assert len(pr2_world.disabled_collision_pairs) == 1128


def test_tracy_semantic_annotation(tracy_world):
    tracy = Tracy.from_world(tracy_world)

    tracy_world._notify_model_change()

    assert len(tracy.manipulators) == 2
    assert len(tracy.manipulator_chains) == 2
    assert len(tracy.sensors) == 1
    assert len(tracy.sensor_chains) == 1
    assert tracy.torso is None
    assert list(tracy.sensor_chains)[0].sensors == tracy.sensors


def test_hsrb_semantic_annotation(hsrb_world):
    hsrb = HSRB.from_world(hsrb_world)

    hsrb_world._notify_model_change()

    assert len(hsrb.manipulators) == 1
    assert len(hsrb.manipulator_chains) == 1
    assert hsrb.neck is not None
    assert len(hsrb.arms) == 1

    assert len(hsrb.sensors) == 5
    assert len(hsrb.sensor_chains) == 2
    assert hsrb.torso is not None


def test_pr2_tighten_dof_velocity_limits_of_1dof_connections(pr2_world):
    pr2 = PR2.from_world(pr2_world)

    # set all joints to vel limit 1
    pr2.tighten_dof_velocity_limits_of_1dof_connections(defaultdict(lambda: 1))

    # try spacial case for specific joint
    new_limits = defaultdict(
        lambda: 0.5, {pr2._world.get_connection_by_name("head_pan_joint"): 23}
    )
    pr2.tighten_dof_velocity_limits_of_1dof_connections(new_limits)
    # if spacial case triggers, but the new limit is above the old one, nothing happens
    assert (
        pr2._world.get_connection_by_name("head_pan_joint").dof.upper_limits.velocity
        == 1
    )
    # new limit is applied to joint without spacial case
    assert (
        pr2._world.get_connection_by_name("head_tilt_joint").dof.upper_limits.velocity
        == 0.5
    )
    # non-spacial case where the old limit is below 1
    assert (
        pr2._world.get_connection_by_name("torso_lift_joint").dof.upper_limits.velocity
        == 0.013
    )
