#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "cpp-logger::cpp-logger" for configuration "Release"
set_property(TARGET cpp-logger::cpp-logger APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(cpp-logger::cpp-logger PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libcpp-logger.so.1.1.0"
  IMPORTED_SONAME_RELEASE "libcpp-logger.so.1"
  )

list(APPEND _cmake_import_check_targets cpp-logger::cpp-logger )
list(APPEND _cmake_import_check_files_for_cpp-logger::cpp-logger "${_IMPORT_PREFIX}/lib/libcpp-logger.so.1.1.0" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
