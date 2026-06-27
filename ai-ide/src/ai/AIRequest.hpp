#pragma once
#include <string>

struct AIRequest {
    std::string mode;
    std::string prompt;
    std::string fileContext;
    std::string selection;
    bool streaming = false;
};
