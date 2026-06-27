#include "WelcomeWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QFrame>

WelcomeWidget::WelcomeWidget(QWidget* parent)
    : QWidget(parent)
{
    // Styling with visual theme matching VS Code dark welcoming styles
    setStyleSheet("QWidget { background-color: #1e1e1e; color: #abb2bf; }"
                  "QLabel#title { color: #61afef; font-family: 'Segoe UI', Arial, sans-serif; font-size: 36px; font-weight: bold; margin-bottom: 5px; }"
                  "QLabel#subtitle { color: #5c6370; font-family: 'Segoe UI', Arial, sans-serif; font-size: 15px; margin-bottom: 25px; }"
                  "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 6px; padding: 12px 24px; font-size: 14px; text-align: left; font-family: 'Segoe UI', Arial; min-width: 280px; margin-bottom: 10px; }"
                  "QPushButton:hover { background-color: #3e4452; color: #ffffff; border-color: #61afef; }"
                  "QPushButton:pressed { background-color: #4b5263; }");

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setAlignment(Qt::AlignCenter);

    auto* container = new QWidget(this);
    auto* layout = new QVBoxLayout(container);
    layout->setContentsMargins(40, 40, 40, 40);
    layout->setAlignment(Qt::AlignCenter);

    auto* titleLabel = new QLabel("AI-IDE", this);
    titleLabel->setObjectName("title");
    titleLabel->setAlignment(Qt::AlignCenter);
    layout->addWidget(titleLabel);

    auto* subtitleLabel = new QLabel("Next-generation C++ development powered by LLVM and Local AI", this);
    subtitleLabel->setObjectName("subtitle");
    subtitleLabel->setAlignment(Qt::AlignCenter);
    layout->addWidget(subtitleLabel);

    // Dark separator line
    auto* line = new QFrame(this);
    line->setFrameShape(QFrame::HLine);
    line->setStyleSheet("background-color: #2c313c; max-height: 1px; margin-bottom: 20px;");
    layout->addWidget(line);

    // Setup action buttons
    auto* newFileBtn = new QPushButton("📄  Create New File", this);
    auto* openFileBtn = new QPushButton("📂  Open Existing File", this);
    auto* openFolderBtn = new QPushButton("📁  Open Project Folder", this);
    auto* buildBtn = new QPushButton("🛠️  Build C++ Project", this);
    auto* settingsBtn = new QPushButton("⚙️  AI Provider Settings", this);

    layout->addWidget(newFileBtn);
    layout->addWidget(openFileBtn);
    layout->addWidget(openFolderBtn);
    layout->addWidget(buildBtn);
    layout->addWidget(settingsBtn);

    mainLayout->addWidget(container);

    // Click mappings
    connect(newFileBtn, &QPushButton::clicked, this, &WelcomeWidget::newFileRequested);
    connect(openFileBtn, &QPushButton::clicked, this, &WelcomeWidget::openFileRequested);
    connect(openFolderBtn, &QPushButton::clicked, this, &WelcomeWidget::openFolderRequested);
    connect(buildBtn, &QPushButton::clicked, this, &WelcomeWidget::buildRequested);
    connect(settingsBtn, &QPushButton::clicked, this, &WelcomeWidget::settingsRequested);
}
