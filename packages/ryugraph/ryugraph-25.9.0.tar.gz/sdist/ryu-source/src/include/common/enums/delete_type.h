#pragma once

#include <cstdint>

namespace ryu {
namespace common {

enum class DeleteNodeType : uint8_t {
    DELETE = 0,
    DETACH_DELETE = 1,
};

} // namespace common
} // namespace ryu
