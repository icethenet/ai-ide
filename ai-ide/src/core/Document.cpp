#include "Document.hpp"
#include <fstream>

Document::Document(const std::string& path) : filePath(path) {
    std::ifstream f(path);
    buffer.assign((std::istreambuf_iterator<char>(f)),
                   std::istreambuf_iterator<char>());
}

std::string Document::getText() const {
    return buffer;
}

void Document::applyEdit(size_t start, size_t end, const std::string& text) {
    buffer.replace(start, end - start, text);
}

void Document::save() {
    std::ofstream f(filePath);
    f << buffer;
}
