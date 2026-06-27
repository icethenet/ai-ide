#pragma once
#include "AIProvider.hpp"
#include <string>

class OllamaProvider : public AIProvider {
public:
    OllamaProvider(const std::string& endpoint);
    AIResponse send(const AIRequest& req) override;

private:
    std::string endpoint;
};
