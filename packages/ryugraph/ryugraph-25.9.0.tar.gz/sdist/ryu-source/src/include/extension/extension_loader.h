#pragma once

#include <string>

#include "common/api.h"

namespace ryu {
namespace main {
class ClientContext;
}
namespace extension {

class RYU_API ExtensionLoader {
public:
    explicit ExtensionLoader(std::string extensionName) : extensionName{std::move(extensionName)} {}

    virtual ~ExtensionLoader() = default;

    virtual void loadDependency(main::ClientContext* context) = 0;

protected:
    std::string extensionName;
};

} // namespace extension
} // namespace ryu
