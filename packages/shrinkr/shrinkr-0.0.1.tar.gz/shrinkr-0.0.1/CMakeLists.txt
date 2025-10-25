cmake_minimum_required(VERSION 3.15)
project(shrinkr)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(MODULE_NAME "_core")

set(SRC_DIR ${CMAKE_SOURCE_DIR}/src)
set(ALGORITHMS_DIR ${CMAKE_SOURCE_DIR}/src/algorithms)
set(INCLUDE_DIR ${CMAKE_SOURCE_DIR}/include)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 REQUIRED)

include_directories(${INCLUDE_DIR})

set(ALGORITHM_SOURCES
  ${ALGORITHMS_DIR}/rle.cpp
)

set(SOURCES
  ${SRC_DIR}/utils.cpp
  ${ALGORITHM_SOURCES}
)

add_executable(${PROJECT_NAME} ${SRC_DIR}/main.cpp ${SOURCES})

pybind11_add_module(${MODULE_NAME} ${SRC_DIR}/bindings.cpp ${SOURCES})

install(TARGETS ${MODULE_NAME} DESTINATION ${PROJECT_NAME})
