//
// Created by haridev on 8/28/22.
//

#ifndef BRAHMA_ENUMERATION_H
#define BRAHMA_ENUMERATION_H
#include <brahma/brahma_config.hpp>
/* Internal Headers */
/* External Headers */
#include <cstdint>

namespace brahma {
enum InterfaceType : uint8_t {
  INTERFACE_POSIX = 0,
  INTERFACE_STDIO = 1,
  INTERFACE_MPIIO = 2,
  INTERFACE_HDF5 = 3
};
}  // namespace brahma
#endif  // BRAHMA_ENUMERATION_H
