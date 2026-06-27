#include "ActionLog.hpp"

void ActionLog::record(const AIAction& action) {
    actions.push_back(action);
}

std::vector<AIAction> ActionLog::list() const {
    return actions;
}
