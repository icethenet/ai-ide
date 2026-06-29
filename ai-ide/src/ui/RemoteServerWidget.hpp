#pragma once
#include <QWidget>
#include <QLineEdit>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QTcpSocket>
#include <QDateTime>

class RemoteServerWidget : public QWidget {
    Q_OBJECT
public:
    explicit RemoteServerWidget(QWidget* parent = nullptr);

signals:
    void openSshRequested(const QString& host, const QString& port, const QString& user);

private slots:
    void testTcpConnection();
    void openSshTerminal();
    void onConnected();
    void onError(QAbstractSocket::SocketError socketError);

private:
    void log(const QString& message);

    QLineEdit* hostInput;
    QLineEdit* portInput;
    QLineEdit* userInput;
    QPushButton* testBtn;
    QPushButton* sshBtn;
    QPlainTextEdit* logEdit;

    QTcpSocket* tcpSocket;
    QDateTime connectionStartTime;
};
