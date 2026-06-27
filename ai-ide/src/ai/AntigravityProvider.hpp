#pragma once
#include "AIProvider.hpp"
#include <string>

class AntigravityProvider : public AIProvider {
public:
    AntigravityProvider(const std::string& apiKey, const std::string& customEndpoint = "");
    AIResponse send(const AIRequest& req) override;

private:
    std::string apiKey;
    std::string endpoint;
};
