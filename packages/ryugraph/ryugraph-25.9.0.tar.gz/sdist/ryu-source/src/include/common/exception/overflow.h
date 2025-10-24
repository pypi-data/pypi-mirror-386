#pragma once

#include "common/api.h"
#include "exception.h"

namespace ryu {
namespace common {

class RYU_API OverflowException : public Exception {
public:
    explicit OverflowException(const std::string& msg) : Exception("Overflow exception: " + msg) {}
};

} // namespace common
} // namespace ryu
