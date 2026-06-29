#pragma once
#include <QString>

struct AIAction {
    QString type;        // "create_file" | "modify_file" | "modify_current_editor" | "insert_at_cursor"
    QString path;        // target file path (relative)
    QString description; // action description
    QString content;     // code content
};
