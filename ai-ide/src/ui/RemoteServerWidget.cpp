#include "RemoteServerWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QLabel>
#include <QStyle>

RemoteServerWidget::RemoteServerWidget(QWidget* parent)
    : QWidget(parent), tcpSocket(new QTcpSocket(this))
{
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(8, 8, 8, 8);
    mainLayout->setSpacing(10);

    auto* headerLabel = new QLabel("Remote Server Manager", this);
    headerLabel->setStyleSheet("QLabel { color: #61afef; font-family: 'Segoe UI', Arial; font-size: 13px; font-weight: bold; }");
    mainLayout->addWidget(headerLabel);

    auto* formLayout = new QFormLayout();
    formLayout->setSpacing(6);

    QString inputStyle = "QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px; font-family: 'Segoe UI', Arial; font-size: 11px; }";

    hostInput = new QLineEdit(this);
    hostInput->setPlaceholderText("e.g. 192.168.1.100");
    hostInput->setText("127.0.0.1");
    hostInput->setStyleSheet(inputStyle);

    portInput = new QLineEdit(this);
    portInput->setPlaceholderText("e.g. 22");
    portInput->setText("22");
    portInput->setStyleSheet(inputStyle);

    userInput = new QLineEdit(this);
    userInput->setPlaceholderText("e.g. ubuntu");
    userInput->setText("ubuntu");
    userInput->setStyleSheet(inputStyle);

    auto* hostLabel = new QLabel("Host:", this);
    hostLabel->setStyleSheet("color: #abb2bf; font-size: 11px;");
    auto* portLabel = new QLabel("Port:", this);
    portLabel->setStyleSheet("color: #abb2bf; font-size: 11px;");
    auto* userLabel = new QLabel("User:", this);
    userLabel->setStyleSheet("color: #abb2bf; font-size: 11px;");

    formLayout->addRow(hostLabel, hostInput);
    formLayout->addRow(portLabel, portInput);
    formLayout->addRow(userLabel, userInput);
    mainLayout->addLayout(formLayout);

    auto* btnLayout = new QHBoxLayout();
    testBtn = new QPushButton("Test TCP", this);
    sshBtn = new QPushButton("Open SSH", this);

    QString btnStyle = "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px; font-family: 'Segoe UI', Arial; font-size: 11px; font-weight: bold; }"
                       "QPushButton:hover { background-color: #3e4452; color: #ffffff; }";
    testBtn->setStyleSheet(btnStyle);
    sshBtn->setStyleSheet("QPushButton { background-color: #61afef; color: #1e1e1e; border: none; border-radius: 4px; padding: 6px; font-family: 'Segoe UI', Arial; font-size: 11px; font-weight: bold; }"
                          "QPushButton:hover { background-color: #528bff; }");

    btnLayout->addWidget(testBtn);
    btnLayout->addWidget(sshBtn);
    mainLayout->addLayout(btnLayout);

    logEdit = new QPlainTextEdit(this);
    logEdit->setReadOnly(true);
    logEdit->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #98c379; border: 1px solid #3e4452; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 10px; }");
    mainLayout->addWidget(logEdit);

    connect(testBtn, &QPushButton::clicked, this, &RemoteServerWidget::testTcpConnection);
    connect(sshBtn, &QPushButton::clicked, this, &RemoteServerWidget::openSshTerminal);

    connect(tcpSocket, &QTcpSocket::connected, this, &RemoteServerWidget::onConnected);
    connect(tcpSocket, &QTcpSocket::errorOccurred, this, &RemoteServerWidget::onError);

    log("Remote Server manager initialized. Ready to connect.");
}

void RemoteServerWidget::log(const QString& message) {
    QString timeStr = QDateTime::currentDateTime().toString("hh:mm:ss");
    logEdit->appendPlainText(QString("[%1] %2").arg(timeStr).arg(message));
}

void RemoteServerWidget::testTcpConnection() {
    QString host = hostInput->text().trimmed();
    int port = portInput->text().toInt();

    if (host.isEmpty() || port <= 0) {
        log("Error: Host or Port is invalid.");
        return;
    }

    log(QString("Testing TCP socket connection to %1:%2...").arg(host).arg(port));
    testBtn->setEnabled(false);
    connectionStartTime = QDateTime::currentDateTime();
    tcpSocket->connectToHost(host, port);
}

void RemoteServerWidget::openSshTerminal() {
    QString host = hostInput->text().trimmed();
    QString port = portInput->text().trimmed();
    QString user = userInput->text().trimmed();

    if (host.isEmpty() || port.toInt() <= 0 || user.isEmpty()) {
        log("Error: Host, Port, or User is invalid for SSH.");
        return;
    }

    log(QString("Opening SSH terminal shell session for %1@%2:%3...").arg(user).arg(host).arg(port));
    emit openSshRequested(host, port, user);
}

void RemoteServerWidget::onConnected() {
    qint64 latency = connectionStartTime.msecsTo(QDateTime::currentDateTime());
    log(QString("TCP connection SUCCESSFUL! Target is ONLINE. Latency: %1ms").arg(latency));
    tcpSocket->disconnectFromHost();
    testBtn->setEnabled(true);
}

void RemoteServerWidget::onError(QAbstractSocket::SocketError socketError) {
    log(QString("TCP connection FAILED: %1").arg(tcpSocket->errorString()));
    testBtn->setEnabled(true);
}
