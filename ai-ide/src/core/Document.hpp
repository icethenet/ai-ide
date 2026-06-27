#pragma once
#include <string>

class Document {
public:
    Document(const std::string& path);
    std::string getText() const;
    void applyEdit(size_t start, size_t end, const std::string& text);
    void save();

private:
    std::string filePath;
    std::string buffer;
};
