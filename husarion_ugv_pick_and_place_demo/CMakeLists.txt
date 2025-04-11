cmake_minimum_required(VERSION 3.8)
project(husarion_ugv_pick_and_place_demo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# find_package(husarion_ugv_gazebo REQUIRED)

install(DIRECTORY launch config worlds models DESTINATION share/${PROJECT_NAME})

ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/${PROJECT_NAME}.sh.in")

ament_package()
