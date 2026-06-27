#include "CppHighlighter.hpp"
#include <QColor>
#include <QFont>
#include <QStringList>

CppHighlighter::CppHighlighter(QTextDocument* parent)
    : QSyntaxHighlighter(parent)
{
    HighlightingRule rule;

    // Keywords (Purple-ish theme matching modern dark UI)
    keywordFormat.setForeground(QColor(198, 120, 221));
    keywordFormat.setFontWeight(QFont::Bold);
    QStringList keywordPatterns;
    keywordPatterns << "\\bchar\\b" << "\\bclass\\b" << "\\bconst\\b"
                    << "\\bdouble\\b" << "\\benum\\b" << "\\bexplicit\\b"
                    << "\\bfloat\\b" << "\\bint\\b" << "\\blong\\b"
                    << "\\boperator\\b" << "\\bprivate\\b" << "\\bprotected\\b"
                    << "\\bpublic\\b" << "\\bshort\\b" << "\\bsignals\\b"
                    << "\\bsigned\\b" << "\\bslots\\b" << "\\bstatic\\b"
                    << "\\bstruct\\b" << "\\btemplate\\b" << "\\btypedef\\b"
                    << "\\btypename\\b" << "\\bunion\\b" << "\\bunsigned\\b"
                    << "\\bvirtual\\b" << "\\bvoid\\b" << "\\bvolatile\\b"
                    << "\\bbool\\b" << "\\bif\\b" << "\\belse\\b"
                    << "\\bfor\\b" << "\\bwhile\\b" << "\\bdo\\b"
                    << "\\breturn\\b" << "\\bswitch\\b" << "\\bcase\\b"
                    << "\\bbreak\\b" << "\\bcontinue\\b" << "\\bdefault\\b"
                    << "\\bnew\\b" << "\\bdelete\\b" << "\\btry\\b"
                    << "\\bcatch\\b" << "\\bthrow\\b" << "\\bnamespace\\b"
                    << "\\busing\\b" << "\\bconstexpr\\b" << "\\bnullptr\\b";
    for (const QString& pattern : keywordPatterns) {
        rule.pattern = QRegularExpression(pattern);
        rule.format = keywordFormat;
        highlightingRules.push_back(rule);
    }

    // Classes / Types (Yellow)
    classFormat.setForeground(QColor(229, 192, 123));
    classFormat.setFontWeight(QFont::Bold);
    rule.pattern = QRegularExpression("\\b[A-Z][a-zA-Z0-9_]*\\b");
    rule.format = classFormat;
    highlightingRules.push_back(rule);

    // Preprocessor directives (Red)
    preprocessorFormat.setForeground(QColor(224, 108, 117));
    rule.pattern = QRegularExpression("^\\s*#\\s*[a-zA-Z]+");
    rule.format = preprocessorFormat;
    highlightingRules.push_back(rule);

    // Functions (Blue)
    functionFormat.setForeground(QColor(97, 175, 239));
    rule.pattern = QRegularExpression("\\b[A-Za-z0-9_]+(?=\\s*\\()");
    rule.format = functionFormat;
    highlightingRules.push_back(rule);

    // Strings (Green)
    quotationFormat.setForeground(QColor(152, 195, 121));
    rule.pattern = QRegularExpression("\".*?\"");
    rule.format = quotationFormat;
    highlightingRules.push_back(rule);

    // Numbers (Orange)
    numberFormat.setForeground(QColor(209, 154, 102));
    rule.pattern = QRegularExpression("\\b\\d+(\\.\\d+)?\\b");
    rule.format = numberFormat;
    highlightingRules.push_back(rule);

    // Single line comments (Gray)
    singleLineCommentFormat.setForeground(QColor(92, 99, 112));
    singleLineCommentFormat.setFontItalic(true);
    rule.pattern = QRegularExpression("//[^\n]*");
    rule.format = singleLineCommentFormat;
    highlightingRules.push_back(rule);

    // Multi-line comments
    multiLineCommentFormat.setForeground(QColor(92, 99, 112));
    multiLineCommentFormat.setFontItalic(true);
    commentStartExpression = QRegularExpression(R"(\/\*)");
    commentEndExpression = QRegularExpression(R"(\*\/)");
}

void CppHighlighter::highlightBlock(const QString& text) {
    for (const auto& rule : highlightingRules) {
        QRegularExpressionMatchIterator matchIterator = rule.pattern.globalMatch(text);
        while (matchIterator.hasNext()) {
            QRegularExpressionMatch match = matchIterator.next();
            setFormat(match.capturedStart(), match.capturedLength(), rule.format);
        }
    }

    setCurrentBlockState(0);

    int startIndex = 0;
    if (previousBlockState() != 1) {
        QRegularExpressionMatch startMatch = commentStartExpression.match(text);
        if (startMatch.hasMatch()) {
            startIndex = startMatch.capturedStart();
        } else {
            startIndex = -1;
        }
    }

    while (startIndex >= 0) {
        QRegularExpressionMatch endMatch = commentEndExpression.match(text, startIndex);
        int commentLength;
        if (!endMatch.hasMatch()) {
            setCurrentBlockState(1);
            commentLength = text.length() - startIndex;
        } else {
            commentLength = endMatch.capturedStart() - startIndex + endMatch.capturedLength();
        }
        setFormat(startIndex, commentLength, multiLineCommentFormat);
        
        if (currentBlockState() == 1) {
            break;
        }
        
        QRegularExpressionMatch nextStartMatch = commentStartExpression.match(text, startIndex + commentLength);
        if (nextStartMatch.hasMatch()) {
            startIndex = nextStartMatch.capturedStart();
        } else {
            startIndex = -1;
        }
    }
}
