##============================================================================
##  The contents of this file are covered by the Viskores license. See
##  LICENSE.txt for details.
##
##  By contributing to this file, all contributors agree to the Developer
##  Certificate of Origin Version 1.1 (DCO 1.1) as stated in DCO.txt.
##============================================================================

##============================================================================
##  Copyright (c) Kitware, Inc.
##  All rights reserved.
##  See LICENSE.txt for details.
##
##  This software is distributed WITHOUT ANY WARRANTY; without even
##  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
##  PURPOSE.  See the above copyright notice for more information.
##============================================================================

# When this file is run by CMake through the find_package command, the
# following targets will exist:
#   viskores::cont       Target that contains most of Viskores
#
#   viskores::rendering  Target that contains all the rendering code
#
#   viskores::filter     Target that contains all of Viskores pre-built filters
#
#   viskores::source     Target that contains all of Viskores pre-built sources
#
#   viskores::tbb        Target that contains tbb related link information
#                    implicitly linked to by `viskores_cont` if tbb is enabled
#
#   viskores::openmp     Target that contains openmp related link information
#                    implicitly linked to by `viskores_cont` if openmp is enabled
#
#   viskores::cuda       Target that contains cuda related link information
#                    implicitly linked to by `viskores_cont` if cuda is enabled
#
# The following local variables will also be defined:
#
#  Viskores_VERSION         Holds the version string of "Major.Minor"
#  Viskores_VERSION_FULL    Holds the version string of "Major.Minor.Patch.GitSha1"
#  Viskores_VERSION_MAJOR   Holds just the major version number
#  Viskores_VERSION_MINOR   Holds just the minor version number
#  Viskores_VERSION_PATCH   Holds just the patch version number
#
#  Viskores_BUILD_SHARED_LIBS     Will be enabled if Viskores was built shared/dynamic
#  Viskores_ENABLE_CUDA           Will be enabled if Viskores was built with CUDA support
#  Viskores_ENABLE_TBB            Will be enabled if Viskores was built with TBB support
#  Viskores_ENABLE_OPENMP         Will be enabled if Viskores was built with OpenMP support
#  Viskores_ENABLE_KOKKOS         Will be enabled if Viskores was built with Kokkos support
#  Viskores_ENABLE_LOGGING        Will be enabled if Viskores was built with logging support
#  Viskores_ENABLE_MPI            Will be enabled if Viskores was built with MPI support
#  Viskores_ENABLE_RENDERING      Will be enabled if Viskores was built with rendering support
#  Viskores_ENABLE_GL_CONTEXT     Will be enabled if Viskores rendering was built with a GL context
#  Viskores_ENABLE_OSMESA_CONTEXT Will be enabled if Viskores rendering was built with a osmesa context
#  Viskores_ENABLE_EGL_CONTEXT    Will be enabled if Viskores rendering was built with a EGL context
#

if (CMAKE_VERSION VERSION_LESS "3.12")
  message(FATAL_ERROR "Viskores requires CMake 3.12+")
endif()
if("${CMAKE_GENERATOR}" MATCHES "Visual Studio" AND
   CMAKE_VERSION VERSION_LESS "3.11")
  message(FATAL_ERROR "Viskores requires CMake 3.11+ when using the Visual Studio Generators")
endif()


####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was ViskoresConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../../" ABSOLUTE)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

# The Viskores version number
set(Viskores_VERSION_MAJOR "1")
set(Viskores_VERSION_MINOR "0")
set(Viskores_VERSION_PATCH "0")
set(Viskores_VERSION_FULL "1.0.0")
set(Viskores_VERSION "1.0")

set(Viskores_BUILD_SHARED_LIBS "ON")
set(Viskores_ENABLE_CUDA "OFF")
set(Viskores_ENABLE_KOKKOS "OFF")
set(Viskores_ENABLE_OPENMP "OFF")
set(Viskores_ENABLE_TBB "OFF")
set(Viskores_ENABLE_LOGGING "ON")
set(Viskores_ENABLE_RENDERING "OFF")
set(Viskores_ENABLE_ANARI "OFF")
set(Viskores_ENABLE_GL_CONTEXT "")
set(Viskores_ENABLE_OSMESA_CONTEXT "")
set(Viskores_ENABLE_EGL_CONTEXT "")
set(Viskores_ENABLE_MPI "OFF")
set(Viskores_ENABLE_TESTING_LIBRARY "ON")
set(Viskores_USE_DEFAULT_TYPES_FOR_ASCENT "OFF")

# This is true when the package is still in the build directory (not installed)
if(CMAKE_CURRENT_LIST_DIR STREQUAL "/opt/glr/vtk/vtk-ci-ext/0/build/vtk-9.5.0.data/headers/cmake/viskores")
  set(Viskores_PACKAGE_IN_BUILD TRUE)
endif()

if(Viskores_PACKAGE_IN_BUILD)
  set_and_check(Viskores_CMAKE_MODULE_PATH "/opt/glr/vtk/vtk-ci-ext/0/ThirdParty/viskores/vtkviskores/viskores/CMake")
else()
  set_and_check(Viskores_CMAKE_MODULE_PATH "${PACKAGE_PREFIX_DIR}/vtk-9.5.0.data/headers/cmake/viskores/cmake")
endif()

include(CMakeFindDependencyMacro)

set(CMAKE_MODULE_PATH_save_viskores "${CMAKE_MODULE_PATH}")
set(PACKAGE_PREFIX_DIR_save_viskores "${PACKAGE_PREFIX_DIR}")
list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_CURRENT_LIST_DIR}")

if (Viskores_ENABLE_TBB)
  find_dependency(TBB)
  if (NOT TBB_FOUND)
    set(Viskores_FOUND 0)
    list(APPEND Viskores_NOT_FOUND_REASON "TBB not found: ${TBB_NOT_FOUND_MESSAGE}")
  endif()
endif()

if (Viskores_ENABLE_OPENMP)
  find_dependency(OpenMP)
  if (NOT OpenMP_FOUND)
    set(Viskores_FOUND 0)
    list(APPEND Viskores_NOT_FOUND_REASON "OpenMP not found: ${OpenMP_NOT_FOUND_MESSAGE}")
  endif()
endif()

if (Viskores_ENABLE_ANARI)
  find_dependency(anari)
  if (NOT anari_FOUND)
    set(Viskores_FOUND 0)
    list(APPEND Viskores_NOT_FOUND_REASON "ANARI not found: ${anari_NOT_FOUND_MESSAGE}")
  endif()
endif()

set(PACKAGE_PREFIX_DIR ${PACKAGE_PREFIX_DIR_save_viskores})

# Load the library exports, but only if not compiling Viskores itself
set_and_check(Viskores_CONFIG_DIR "${PACKAGE_PREFIX_DIR}/vtk-9.5.0.data/headers/cmake/viskores")
set(VISKORES_FROM_INSTALL_DIR FALSE)
if(NOT "${CMAKE_BINARY_DIR}" STREQUAL "/opt/glr/vtk/vtk-ci-ext/0/build/ThirdParty/viskores/vtkviskores/viskores")
  set(VISKORES_FROM_INSTALL_DIR TRUE)
  include(${Viskores_CONFIG_DIR}/ViskoresTargets.cmake)

  if(DEFINED PACKAGE_FIND_VERSION AND PACKAGE_FIND_VERSION VERSION_LESS 2.0)
    add_library(viskores_cont ALIAS viskores::cont)
    add_library(viskores_filter ALIAS viskores::filter)
    add_library(viskores_io ALIAS viskores::io)
    add_library(viskores_rendering ALIAS viskores::rendering)
    add_library(viskores_source ALIAS viskores::source)
    add_library(viskores_worklet ALIAS viskores::worklet)
  endif()
endif()

# Once we can require CMake 3.15 for all cuda builds we can
# replace this with setting `cuda_architecture_flags` as part of the
# EXPORT_PROPERTIES of the viskores::cuda target
if(Viskores_ENABLE_CUDA AND VISKORES_FROM_INSTALL_DIR)
  # Canonical way of setting CUDA arch
  if(CMAKE_VERSION VERSION_GREATER_EQUAL 3.18)
    set_target_properties(viskores::cuda PROPERTIES CUDA_ARCHITECTURES "")
  endif()

  set_target_properties(viskores::cuda PROPERTIES
    # Legacy way of setting CUDA arch
    cuda_architecture_flags ""
    requires_static_builds TRUE)

  # If Viskores is built with 3.18+ and the consumer is < 3.18 we need to drop
  # these properties as they break the Viskores cuda flag logic
  if(CMAKE_VERSION VERSION_LESS 3.18)
    set_target_properties(viskores::cuda PROPERTIES INTERFACE_LINK_OPTIONS "")
  endif()
endif()

# Viskores requires some CMake Find modules not included with CMake, so
# include the CMake modules distributed with Viskores.
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH_save_viskores} ${Viskores_CMAKE_MODULE_PATH})
unset(CMAKE_MODULE_PATH_save_viskores)

if(Viskores_ENABLE_CUDA)
  if (CMAKE_VERSION VERSION_LESS 3.13)
    message(FATAL_ERROR "Viskores with CUDA requires CMake 3.13+")
  endif()
endif()

# This includes a host of functions used by Viskores CMake.
include(ViskoresWrappers)
include(ViskoresRenderingContexts)

# Setup diy magic of chosing the appropriate mpi/no_mpi library to link against
include(ViskoresDIYUtils)
viskores_diy_init_target()
