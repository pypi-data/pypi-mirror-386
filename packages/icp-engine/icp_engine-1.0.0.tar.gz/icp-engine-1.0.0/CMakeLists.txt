cmake_minimum_required(VERSION 3.26)

project(
  ICP_ENGINE
  VERSION 1.0.0
  LANGUAGES CXX
  DESCRIPTION "ICP Engine - Binary Analysis and Protection Detection"
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_CXX_EXTENSIONS OFF)
set(VCPKG_MANIFEST_MODE OFF)
set(CXX_STANDARD 20)

set(DIE_ROOT_DIR ${CMAKE_CURRENT_LIST_DIR})

list(APPEND CMAKE_MODULE_PATH "${DIE_ROOT_DIR}/cmake")
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

add_subdirectory(python)
