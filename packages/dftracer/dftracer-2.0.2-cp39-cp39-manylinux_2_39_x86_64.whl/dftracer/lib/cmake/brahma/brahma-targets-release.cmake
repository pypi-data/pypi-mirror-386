#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "brahma" for configuration "Release"
set_property(TARGET brahma APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(brahma PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libbrahma.so.2.3.0"
  IMPORTED_SONAME_RELEASE "libbrahma.so.1"
  )

list(APPEND _cmake_import_check_targets brahma )
list(APPEND _cmake_import_check_files_for_brahma "${_IMPORT_PREFIX}/lib/libbrahma.so.2.3.0" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
