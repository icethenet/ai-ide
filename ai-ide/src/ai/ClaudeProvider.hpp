#pragma once
#include "AIProvider.hpp"
#include <string>

class ClaudeProvider : public AIProvider {
public:
    ClaudeProvider(const std::string& apiKey, const std::string& customEndpoint = "");
    AIResponse send(const AIRequest& req) override;

private:
    std::string apiKey;
    std::string endpoint;
};
