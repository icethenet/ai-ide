#include "GitClient.hpp"
#include <iostream>

GitClient::GitClient(const std::string& path)
    : repoPath(path)
{
}

std::vector<GitStatusEntry> GitClient::status() {
    std::cout << "[Git] status in " << repoPath << std::endl;
    return {};
}

void GitClient::add(const std::string& path) {
    std::cout << "[Git] add " << path << std::endl;
}

void GitClient::commit(const std::string& message) {
    std::cout << "[Git] commit: " << message << std::endl;
}

void GitClient::push() {
    std::cout << "[Git] push from " << repoPath << std::endl;
}
