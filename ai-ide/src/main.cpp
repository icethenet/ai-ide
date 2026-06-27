#include <QApplication>
#include "ui/EditorWindow.hpp"

int main(int argc, char *argv[]) {
    QApplication::addLibraryPath("C:/Qt/6.11.1/llvm-mingw_64/plugins");
    QApplication app(argc, argv);
    EditorWindow w;
    w.show();
    return app.exec();
}
