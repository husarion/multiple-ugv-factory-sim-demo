#!/usr/bin/env python3

# Copyright 2024 Husarion sp. z o.o.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import SetUseSimTime
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import ReplaceString
from launch_ros.actions import Node
from launch.actions import ExecuteProcess


def generate_launch_description():
    grasp_config = PathJoinSubstitution(
        [
            FindPackageShare("husarion_ugv_pick_and_place_demo"),
            "config",
            "grasp_service_config.yaml",
        ]
    )

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("husarion_ugv_gazebo"),
                    "launch",
                    "simulation.launch.py",
                ]
            )
        ),
        launch_arguments={
            "use_rviz": "False",
            "gz_log_level": "1",
            "namespace": "panther",
            "robot_model": "panther",
            "gz_world": PathJoinSubstitution(
                [
                    FindPackageShare("husarion_ugv_pick_and_place_demo"),
                    "worlds",
                    "industrial-warehouse_with_outside.sdf",
                ]
            ),
            "gz_gui": PathJoinSubstitution(
                [
                    FindPackageShare("husarion_ugv_pick_and_place_demo"),
                    "config",
                    "gzgui.config",
                ]
            ),
            "components_config_path": PathJoinSubstitution(
                [
                    FindPackageShare("husarion_ugv_pick_and_place_demo"),
                    "config",
                    "panther_components.yaml",
                ]
            ),  # panther
            "x": "-6.2",  # panther
            "y": "9.25",
            "yaw": "3.14",
        }.items(),
    )

    simulate_lynx = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("husarion_ugv_gazebo"),
                    "launch",
                    "simulate_robot.launch.py",
                ]
            )
        ),
        launch_arguments={
            "namespace": "lynx",
            "robot_model": "lynx",
            "x": "-6.2",
            "y": "6.25",
            "yaw": "3.14",
            "wheel_type": "WH05",
            "wheel_config_path": PathJoinSubstitution(
                [FindPackageShare("husarion_ugv_description"), "config", "WH05.yaml"]
            ),
            "components_config_path": PathJoinSubstitution(
                [
                    FindPackageShare("husarion_ugv_pick_and_place_demo"),
                    "config",
                    "lynx_components.yaml",
                ]
            ),
            "controller_config_path": PathJoinSubstitution(
                [
                    FindPackageShare("husarion_ugv_controller"),
                    "config",
                    "WH05_controller.yaml",
                ]
            ),
        }.items(),
    )

    connect_maps_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="connect_maps_tf",
        output="screen",
        parameters=[{"use_sim_time": True}],
        arguments=[
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "0.0",
            "panther/map",
            "lynx/map",
        ],
    )



    laser_filter_config = PathJoinSubstitution(
        [
            FindPackageShare("husarion_ugv_pick_and_place_demo"),
            "config",
            "laser_filter.yaml",
        ]
    )

    laser_filter_node = Node(
        package="laser_filters",
        executable="scan_to_scan_filter_chain",
        parameters=[
            laser_filter_config,
        ],
        namespace="lynx",
    )

    spawn_lynx_with_delay = TimerAction(
        period=20.0, actions=[simulate_lynx, connect_maps_tf, laser_filter_node]
    )

    send_panther_manipulator_to_home_position = ExecuteProcess(
        cmd=[
            "ros2",
            "topic",
            "pub",
            "/panther/panther_ur5e_joint_trajectory_controller/joint_trajectory",
            "trajectory_msgs/msg/JointTrajectory",
            "{"
            "joint_names: ['ur5e_shoulder_pan_joint', 'ur5e_shoulder_lift_joint', 'ur5e_elbow_joint',"
            "'ur5e_wrist_1_joint', 'ur5e_wrist_2_joint', 'ur5e_wrist_3_joint'],"
            "points: "
            "[{"
            "positions: [0.0, -3.4, 2.8, -1.57, 3.14, 0.0],"
            "time_from_start: {sec: 2, nanosec: 0}"
            "}]"
            "}",
            "-t 10",
        ],
        output="screen",
        name="send_panther_manipulator_to_home_position",
    )

    grasp_service_node = Node(
        package="ros2_grasp_service",
        executable="ros2_grasp_service",
        parameters=[grasp_config, {"use_sim_time": True}],
        emulate_tty=True,
        namespace="panther",
    )

    delay_send_manipulators_to_home_position = TimerAction(
        period=18.0,
        actions=[
            send_panther_manipulator_to_home_position,
        ],
    )

    actions = [
        # Sets use_sim_time for all nodes started below (doesn't work for nodes started from ignition gazebo)
        SetUseSimTime(True),
        simulation,
        grasp_service_node,
        spawn_lynx_with_delay,
        delay_send_manipulators_to_home_position,
    ]

    return LaunchDescription(actions)
