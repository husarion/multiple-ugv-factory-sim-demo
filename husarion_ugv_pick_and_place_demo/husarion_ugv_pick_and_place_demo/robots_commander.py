import time
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.node import Node
from std_srvs.srv import Empty, Trigger
from opennav_docking_msgs.action import UndockRobot, DockRobot
from rclpy.action import ActionClient
import math
from copy import copy
import panther_toy_wrapper


def quaternion_from_euler(roll, pitch, yaw):
    """
    Convert Euler angles to a quaternion.

    :param roll: Roll angle in radians
    :param pitch: Pitch angle in radians
    :param yaw: Yaw angle in radians
    :return: A tuple representing the quaternion (x, y, z, w)
    """

    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    qw = cy * cp * cr + sy * sp * sr
    qx = cy * cp * sr - sy * sp * cr
    qy = sy * cp * sr + cy * sp * cr
    qz = sy * cp * cr - cy * sp * sr

    return (qx, qy, qz, qw)


def create_station_pose():
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = "panther/map"
    goal_pose.pose.position.x = -3.3
    goal_pose.pose.position.y = 10.0
    goal_pose.pose.position.z = 0.0
    goal_pose.pose.orientation.x = 0.0
    goal_pose.pose.orientation.y = 0.0
    goal_pose.pose.orientation.z = -1.0
    goal_pose.pose.orientation.w = 0.0
    return goal_pose


def create_station_pose_lynx():
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = "lynx/map"
    goal_pose.pose.position.x = -3.5
    goal_pose.pose.position.y = 8.92
    goal_pose.pose.position.z = 0.0

    qx, qy, qz, qw = quaternion_from_euler(0.0, 0.0, 1.57)

    goal_pose.pose.orientation.x = qx
    goal_pose.pose.orientation.y = qy
    goal_pose.pose.orientation.z = qz
    goal_pose.pose.orientation.w = qw

    return goal_pose

def create_pickup_pose():
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = "panther/map"
    goal_pose.pose.position.x = -19.5
    goal_pose.pose.position.y = 11.0
    goal_pose.pose.position.z = 0.0
    qx, qy, qz, qw = quaternion_from_euler(0.0, 0.0, -3.14)

    goal_pose.pose.orientation.x = qx
    goal_pose.pose.orientation.y = qy
    goal_pose.pose.orientation.z = qz
    goal_pose.pose.orientation.w = qw
    return goal_pose

def pick_and_place(nav):
    pick_service = nav.create_client(Empty, "/panther/pick")
    place_service = nav.create_client(Empty, "/panther/place")
    while not pick_service.wait_for_service(timeout_sec=1.0):
        nav.get_logger().info("Waiting for pick service...")
    while not place_service.wait_for_service(timeout_sec=1.0):
        nav.get_logger().info("Waiting for place service...")
    nav.get_logger().info("Pick and place services are available.")
    pick_request = Empty.Request()
    place_request = Empty.Request()
    nav.get_logger().info("Sending pick request...")
    future = pick_service.call_async(pick_request)
    rclpy.spin_until_future_complete(nav, future)
    if future.result() is not None:
        nav.get_logger().info("Pick request succeeded.")
    else:
        nav.get_logger().error("Pick request failed.")
    nav.get_logger().info("Sending place request...")
    future = place_service.call_async(place_request)
    rclpy.spin_until_future_complete(nav, future)
    if future.result() is not None:
        nav.get_logger().info("Place request succeeded.")
    else:
        nav.get_logger().error("Place request failed.")


def reset_estop(nav):
    """
    Resets the robot's emergency stop.

    :param nav: A ROS 2 node or object with rclpy context and executor
    """
    namespace = nav.get_namespace()
    estop_reset_service = nav.create_client(
        Trigger, f"{namespace}/hardware/e_stop_reset"
    )
    while not estop_reset_service.wait_for_service(timeout_sec=1.0):
        nav.get_logger().info("Waiting for e-stop reset service...")
    nav.get_logger().info("E-stop reset service is available.")

    reset_request = Trigger.Request()
    nav.get_logger().info("Sending e-stop reset request...")
    future = estop_reset_service.call_async(reset_request)
    rclpy.spin_until_future_complete(nav, future)
    if future.result() is not None:
        nav.get_logger().info("E-stop reset succeeded.")
    else:
        nav.get_logger().error("E-stop reset failed.")


def undock_robot(nav, dock_type=None, max_undocking_time=30.0, wait=True):
    """
    Sends an undocking goal to the navigation system.

    :param nav: A ROS 2 node or object with rclpy context and executor
    :param dock_type: Optional string to specify the type of dock
    :param max_undocking_time: Maximum allowed undocking time in seconds
    :return: True if undocking succeeded, False otherwise
    """

    # Create an ActionClient if it's not already part of nav
    namespace = nav.get_namespace()
    action_client = ActionClient(nav, UndockRobot, f"{namespace}/undock_robot")

    if not action_client.wait_for_server(timeout_sec=5.0):
        nav.get_logger().error("Undock action server not available")
        return False

    # Create goal message
    goal_msg = UndockRobot.Goal()
    if dock_type is not None:
        goal_msg.dock_type = dock_type
    goal_msg.max_undocking_time = max_undocking_time

    # Send goal and wait for result
    future = action_client.send_goal_async(goal_msg)
    rclpy.spin_until_future_complete(nav, future)
    goal_handle = future.result()

    if not goal_handle.accepted:
        nav.get_logger().warn("Undock goal was rejected")
        return False

    if not wait:
        return True
    
    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(nav, result_future)
    result = result_future.result().result

    if result.success:
        nav.get_logger().info(f"Robot undocked successfully from {goal_msg.dock_type}")
        return True
    else:
        nav.get_logger().error(
            f"Failed to undock: Error code {result.error_code} from {goal_msg.dock_type}"
        )
        return False


def dock_robot(nav, dock_name=None, max_docking_time=30.0, wait=True):
    """
    Sends a docking goal to the navigation system.

    :param nav: A ROS 2 node or object with rclpy context and executor
    :param dock_name: Optional string to specify the name of the dock
    :param max_docking_time: Maximum allowed docking time in seconds
    :return: True if docking succeeded, False otherwise
    """

    # Create an ActionClient if it's not already part of nav
    namespace = nav.get_namespace()
    action_client = ActionClient(nav, DockRobot, f"{namespace}/dock_robot")

    if not action_client.wait_for_server(timeout_sec=5.0):
        nav.get_logger().error("Dock action server not available")
        return False

    # Create goal message
    goal_msg = DockRobot.Goal()
    if dock_name is not None:
        goal_msg.dock_id = dock_name
    goal_msg.max_staging_time = max_docking_time
    goal_msg.navigate_to_staging_pose = True
    goal_msg.dock_type = "charging_dock"

    # Send goal and wait for result
    future = action_client.send_goal_async(goal_msg)
    rclpy.spin_until_future_complete(nav, future)
    goal_handle = future.result()

    if not goal_handle.accepted:
        nav.get_logger().warn("Dock goal was rejected")
        return False

    if not wait:
        return True

    result_future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(nav, result_future)

    result = result_future.result().result

    if result.success:
        nav.get_logger().info(f"Robot docked successfully to { dock_name }")
        return True
    else:
        nav.get_logger().error(
            f"Failed to dock: Error code {result.error_code} to {dock_name}"
        )
        return False


def navigate(nav, goal_pose, timeout=600, wait=True):
    nav.goToPose(goal_pose)
    
    if not wait:
        return
    
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if (
            feedback and feedback.navigation_time.sec > timeout
        ):  # Timeout after 600 seconds
            nav.cancelTask()
            print("Navigation task canceled due to timeout.")
            break

    # Check the result of the navigation task
    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        print("Goal succeeded!")
    elif result == TaskResult.CANCELED:
        print("Goal was canceled!")
    elif result == TaskResult.FAILED:
        print("Goal failed!")


def main():
    rclpy.init()

    # Create a BasicNavigator instance
    panther = BasicNavigator(node_name="robot_navigator", namespace="panther")
    panther.waitUntilNav2Active()
    panther.get_logger().info("BasicNavigator created")

    lynx = BasicNavigator(node_name="robot_navigator", namespace="lynx")
    lynx.get_logger().info("BasicNavigator created")
    lynx.waitUntilNav2Active()

    reset_estop(panther)
    reset_estop(lynx)

    lynx_station_pose = create_station_pose_lynx()
    lynx_undock_station_pose = create_station_pose_lynx()
    lynx_undock_station_pose.pose.position.y -= 0.6
    lynx_pickup_pose = create_pickup_pose()

    while True:
        undock_robot(panther,max_undocking_time=40.0, wait=False)
        undock_robot(lynx, max_undocking_time=40.0, wait=True)
        panther_toy_wrapper.create_panther_toy()
        dock_robot(panther, dock_name="panther_toy", max_docking_time=30.0, wait=False)
        time.sleep(25.0)  # Give some time for the panther to dock before navigating lynx
        navigate(lynx, lynx_undock_station_pose, timeout=600)
        navigate(lynx, lynx_station_pose, timeout=600)
        pick_and_place(panther)

        navigate(lynx, lynx_undock_station_pose, timeout=600, wait=False)
        undock_robot(panther)
        dock_robot(panther, dock_name="main", max_docking_time=30.0, wait=False)
        navigate(lynx, lynx_pickup_pose, timeout=600)
        panther_toy_wrapper.remove_panther_toy()
        dock_robot(lynx, "lynx_main", max_docking_time=60.0)

    rclpy.shutdown()


if __name__ == "__main__":
    main()
