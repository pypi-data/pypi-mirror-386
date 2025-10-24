#pragma once
#include <string>

namespace ryu {
namespace parser {

struct YieldVariable {
    std::string name;
    std::string alias;

    YieldVariable(std::string name, std::string alias)
        : name{std::move(name)}, alias{std::move(alias)} {}
    bool hasAlias() const { return alias != ""; }
};

} // namespace parser
} // namespace ryu
