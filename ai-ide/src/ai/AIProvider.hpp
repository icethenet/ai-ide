#pragma once
#include "AIRequest.hpp"
#include "AIResponse.hpp"

class AIProvider {
public:
    virtual ~AIProvider() = default;
    virtual AIResponse send(const AIRequest& req) = 0;
};
