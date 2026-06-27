#pragma once
#include <string>
#include <vector>

struct GitStatusEntry {
    std::string path;
    std::string status;
};

class GitClient {
public:
    explicit GitClient(const std::string& repoPath);

    std::vector<GitStatusEntry> status();
    void commit(const std::string& message);
    void add(const std::string& path);
    void push();

private:
    std::string repoPath;
};
