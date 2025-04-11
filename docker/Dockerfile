ARG ROS_DISTRO=humble

FROM husarion/husarion-ugv-gazebo:humble-2.2.1-20250331
ARG BUILD_TEST=OFF

ENV HUSARION_ROS_BUILD_TYPE=simulation

STOPSIGNAL SIGINT

WORKDIR /ros2_ws
COPY . src/husarion_ugv_pick_and_place_demo

RUN apt-get update  && \
    apt-get install -y \
        ros-dev-tools ros-humble-effort-controllers ros-humble-position-controllers ros-humble-gripper-controllers && \
    # Install dependencies
    # rosdep init && \
    rosdep update --rosdistro $ROS_DISTRO && \
    rosdep install --from-paths src -y -i && \
    # Build
    source /opt/ros/$ROS_DISTRO/setup.bash && \
    colcon build --symlink-install --packages-up-to husarion_ugv_pick_and_place_demo --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=$BUILD_TEST && \
    # Get version
    echo $(cat /ros2_ws/src/husarion_ugv_ros/husarion_ugv/package.xml | grep '<version>' | sed -r 's/.*<version>([0-9]+.[0-9]+.[0-9]+)<\/version>/\1/g') >> /version.txt && \
    # Size optimization
    export SUDO_FORCE_REMOVE=yes && \
    apt-get remove -y \
        ros-dev-tools && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
