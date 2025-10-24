#pragma once

#include "pybind_include.h"

namespace ryu {
namespace pyarrow {

class Table : public py::object {
public:
    explicit Table(const py::object& o) : py::object(o, borrowed_t{}) {}

public:
    static bool check_(const py::handle& object) { return !py::none().is(object); }
};
} // namespace pyarrow
} // namespace ryu
