#pragma once
#include "Patch.hpp"
#include <string>
#include <vector>

struct AIAction {
    std::string id;
    std::string provider;
    std::string model;
    std::string prompt;
    std::string timestamp;
    std::vector<Patch> patches;
    bool applied;
};

class ActionLog {
public:
    void record(const AIAction& action);
    std::vector<AIAction> list() const;

private:
    std::vector<AIAction> actions;
};
