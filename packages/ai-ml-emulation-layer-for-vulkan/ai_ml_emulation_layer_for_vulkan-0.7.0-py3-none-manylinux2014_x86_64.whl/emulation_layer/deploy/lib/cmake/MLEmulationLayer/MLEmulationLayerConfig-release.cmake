#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "MLEmulationLayer::VkLayer_Graph" for configuration "Release"
set_property(TARGET MLEmulationLayer::VkLayer_Graph APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MLEmulationLayer::VkLayer_Graph PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libVkLayer_Graph.so"
  IMPORTED_SONAME_RELEASE "libVkLayer_Graph.so"
  )

list(APPEND _cmake_import_check_targets MLEmulationLayer::VkLayer_Graph )
list(APPEND _cmake_import_check_files_for_MLEmulationLayer::VkLayer_Graph "${_IMPORT_PREFIX}/lib/libVkLayer_Graph.so" )

# Import target "MLEmulationLayer::VkLayer_Tensor" for configuration "Release"
set_property(TARGET MLEmulationLayer::VkLayer_Tensor APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(MLEmulationLayer::VkLayer_Tensor PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libVkLayer_Tensor.so"
  IMPORTED_SONAME_RELEASE "libVkLayer_Tensor.so"
  )

list(APPEND _cmake_import_check_targets MLEmulationLayer::VkLayer_Tensor )
list(APPEND _cmake_import_check_files_for_MLEmulationLayer::VkLayer_Tensor "${_IMPORT_PREFIX}/lib/libVkLayer_Tensor.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
