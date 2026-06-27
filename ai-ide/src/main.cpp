#include <QApplication>
#include "ui/EditorWindow.hpp"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    EditorWindow w;
    w.show();
    return app.exec();
}
