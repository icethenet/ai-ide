#pragma once
#include <string>
#include <optional>
#include "Patch.hpp"

struct AIResponse {
    std::string text;
    std::optional<Patch> patch;
};
