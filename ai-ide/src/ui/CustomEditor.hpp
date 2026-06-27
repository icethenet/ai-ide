#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QString>

class CodeEditor;
class CppHighlighter;

class CustomEditor : public QWidget {
    Q_OBJECT
public:
    explicit CustomEditor(QWidget* parent = nullptr);

    void openFile(const QString& path);
    void saveFile();
    void saveAsFile();
    QString currentFilePath() const;

signals:
    void fileChanged(const QString& path);
    void closeRequested();

private:
    CodeEditor* editor;
    QPushButton* closeButton;
    QPushButton* saveAsButton;
    QString filePath;
    CppHighlighter* highlighter;
};

class CodeEditor : public QPlainTextEdit {
    Q_OBJECT
public:
    explicit CodeEditor(QWidget* parent = nullptr);

    void lineNumberAreaPaintEvent(QPaintEvent* event);
    int lineNumberAreaWidth();

protected:
    void resizeEvent(QResizeEvent* event) override;

private slots:
    void updateLineNumberAreaWidth(int newBlockCount);
    void highlightCurrentLine();
    void updateLineNumberArea(const QRect& rect, int dy);

private:
    QWidget* lineNumberArea;
};

class LineNumberArea : public QWidget {
public:
    explicit LineNumberArea(CodeEditor* editor) : QWidget(editor), codeEditor(editor) {}

    QSize sizeHint() const override {
        return QSize(codeEditor->lineNumberAreaWidth(), 0);
    }

protected:
    void paintEvent(QPaintEvent* event) override {
        codeEditor->lineNumberAreaPaintEvent(event);
    }

private:
    CodeEditor* codeEditor;
};
