#pragma once
#include "AIProvider.hpp"
#include <string>

class GeminiProvider : public AIProvider {
public:
    GeminiProvider(const std::string& apiKey);
    AIResponse send(const AIRequest& req) override;

private:
    std::string apiKey;
};
