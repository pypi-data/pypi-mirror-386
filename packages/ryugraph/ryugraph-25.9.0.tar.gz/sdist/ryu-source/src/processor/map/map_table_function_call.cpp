#include "planner/operator/logical_table_function_call.h"
#include "processor/plan_mapper.h"

using namespace ryu::planner;
using namespace ryu::common;

namespace ryu {
namespace processor {

std::unique_ptr<PhysicalOperator> PlanMapper::mapTableFunctionCall(
    const LogicalOperator* logicalOperator) {
    auto& call = logicalOperator->constCast<LogicalTableFunctionCall>();
    auto getPhysicalPlanFunc = call.getTableFunc().getPhysicalPlanFunc;
    KU_ASSERT(getPhysicalPlanFunc);
    auto res = getPhysicalPlanFunc(this, logicalOperator);
    logicalOpToPhysicalOpMap.insert({logicalOperator, res.get()});
    return res;
}

} // namespace processor
} // namespace ryu
