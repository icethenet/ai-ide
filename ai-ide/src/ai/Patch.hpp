#pragma once
#include <string>
#include <vector>

struct PatchEdit {
    size_t start;
    size_t end;
    std::string oldText;
    std::string newText;
};

struct Patch {
    std::string filePath;
    std::vector<PatchEdit> edits;
};
