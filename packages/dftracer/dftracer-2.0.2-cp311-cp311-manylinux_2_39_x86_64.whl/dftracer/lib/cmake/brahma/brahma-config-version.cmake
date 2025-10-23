#-----------------------------------------------------------------------------
# Version file for install directory
#-----------------------------------------------------------------------------
set(PACKAGE_VERSION 2.3.0)

if ("${PACKAGE_FIND_VERSION_MAJOR}" EQUAL 2)
    set(PACKAGE_VERSION_COMPATIBLE 1)
    if ("${PACKAGE_FIND_VERSION_PATCH}" EQUAL 0)
        set(PACKAGE_VERSION_EXACT 1)
    endif ()
endif ()
