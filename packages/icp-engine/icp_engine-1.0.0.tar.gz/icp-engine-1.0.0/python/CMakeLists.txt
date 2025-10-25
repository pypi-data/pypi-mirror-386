project(
    icp_engine
    LANGUAGES CXX
    VERSION 1.0.0
)

find_package(Python 3
    REQUIRED COMPONENTS Interpreter Development.Module
    OPTIONAL_COMPONENTS Development.SABIModule
)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

execute_process(
    COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE NB_DIR)
list(APPEND CMAKE_PREFIX_PATH "${NB_DIR}")

find_package(nanobind CONFIG REQUIRED)
find_package(DieLibrary REQUIRED)

set(DIE_PYTHON_ROOT_DIR ${DIE_ROOT_DIR}/python)
set(DIELIB_BASE_ROOT ${dielibrary_SOURCE_DIR})
set(DIE_BASE_ROOT "${dielibrary_SOURCE_DIR}/dep/Detect-It-Easy")

file(STRINGS ${DIELIB_BASE_ROOT}/release_version.txt DIELIB_VERSION)
file(STRINGS ${DIE_BASE_ROOT}/die_version.txt DIE_VERSION)

nanobind_add_module(_icp_engine
        ./src/icp_engine.cpp
)

add_dependencies(_icp_engine die)

target_include_directories(
    _icp_engine
    PRIVATE
        ${DIE_PYTHON_ROOT_DIR}/inc
        ${DIELIB_BASE_ROOT}/src/include
)

if(MSVC)
    # Disable MSVC `min` & `max` macros for `die` (breaks Qt)
    target_compile_definitions(die PUBLIC NOMINMAX)
endif()

if(APPLE)
    target_link_libraries(_icp_engine PRIVATE dl "-framework CoreFoundation")
    target_link_options(_icp_engine PRIVATE -Wl,-rpath,$ORIGIN/lib)
endif()

if(LINUX)
    target_link_options(_icp_engine PRIVATE -Wl,-rpath,$ORIGIN/lib)
endif()

target_compile_definitions(_icp_engine
    PRIVATE
        DIE_VERSION="${DIE_VERSION}"
        DIELIB_VERSION="${DIELIB_VERSION}"
)

target_link_libraries(_icp_engine PRIVATE $<TARGET_FILE:die> $<TARGET_PROPERTY:die,LINK_LIBRARIES>)
target_link_libraries(_icp_engine PRIVATE Qt6::Core)
target_link_libraries(_icp_engine PRIVATE Qt6::Qml)
target_link_libraries(_icp_engine PRIVATE Qt6::Concurrent)
target_link_libraries(_icp_engine PRIVATE Qt6::Network)

install(DIRECTORY icp_engine DESTINATION .)
install(TARGETS _icp_engine DESTINATION icp_engine/)
install(TARGETS die DESTINATION icp_engine/)
install(DIRECTORY ${DIELIB_BASE_ROOT}/dep/Detect-It-Easy/db DESTINATION icp_engine/db)
install(DIRECTORY ${DIELIB_BASE_ROOT}/dep/Detect-It-Easy/db_custom DESTINATION icp_engine/db)

if(LINUX OR APPLE)
    install(
        DIRECTORY
            ${Qt6_DIR}/../../
        DESTINATION
            icp_engine/lib
        FILES_MATCHING
            PATTERN "libQt6Core.*"
            PATTERN "libQt6Qml.*"
            PATTERN "libQt6Concurrent.*"
            PATTERN "libQt6Network.*"
            PATTERN "libicui18n.*"
            PATTERN "libicuuc.*"
            PATTERN "libicudata.*"
            PATTERN "cmake" EXCLUDE
            PATTERN "objects-*" EXCLUDE
            PATTERN "pkgconfig" EXCLUDE
    )
else()
    install(
        DIRECTORY
            ${Qt6_DIR}/../../../bin/
        DESTINATION
            icp_engine/
        FILES_MATCHING
            PATTERN "Qt6Core.*"
            PATTERN "Qt6Qml.*"
            PATTERN "Qt6Concurrent.*"
            PATTERN "Qt6Network.*"
    )
endif()