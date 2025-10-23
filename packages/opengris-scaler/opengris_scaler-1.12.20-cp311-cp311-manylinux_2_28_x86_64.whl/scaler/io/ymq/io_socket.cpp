#include "scaler/io/ymq/io_socket.h"

#include <algorithm>
#include <expected>
#include <memory>
#include <optional>
#include <ranges>
#include <utility>
#include <vector>

#include "scaler/io/ymq/error.h"
#include "scaler/io/ymq/event_loop_thread.h"
#include "scaler/io/ymq/event_manager.h"
#include "scaler/io/ymq/message_connection_tcp.h"
#include "scaler/io/ymq/network_utils.h"
#include "scaler/io/ymq/tcp_client.h"
#include "scaler/io/ymq/tcp_server.h"
#include "scaler/io/ymq/typedefs.h"

namespace scaler {
namespace ymq {

IOSocket::IOSocket(
    std::shared_ptr<EventLoopThread> eventLoopThread, Identity identity, IOSocketType socketType) noexcept
    : _eventLoopThread(eventLoopThread)
    , _identity(std::move(identity))
    , _socketType(std::move(socketType))
    , _pendingRecvMessages(std::make_shared<std::queue<RecvMessageCallback>>())
    , _stopped {false}
    , _connectorDisconnected {false}
{
}

void IOSocket::sendMessage(Message message, SendMessageCallback onMessageSent) noexcept
{
    _eventLoopThread->_eventLoop.executeNow(
        [this, message = std::move(message), callback = std::move(onMessageSent)] mutable {
            if (_stopped) {
                callback(std::unexpected {Error::ErrorCode::IOSocketStopRequested});
                return;
            }
            if (_connectorDisconnected) {
                callback(std::unexpected {Error::ErrorCode::ConnectorSocketClosedByRemoteEnd});
                return;
            }
            if (!message.address.data() && this->socketType() == IOSocketType::Binder) {
                callback(std::unexpected {Error::ErrorCode::BinderSendMessageWithNoAddress});
            }

            MessageConnectionTCP* conn = nullptr;

            std::string address = std::string((char*)message.address.data(), message.address.len());
            if (this->socketType() == IOSocketType::Connector) {
                address = "";
            } else if (this->socketType() == IOSocketType::Multicast) {
                callback({});  // SUCCESS
                for (const auto& [addr, conn]: _identityToConnection) {
                    // TODO: Currently doing N copies of the messages. Find a place to
                    // store this message and pass in reference.
                    if (addr.starts_with(address))
                        conn->sendMessage(message, [](auto) {});
                }
                return;
            }

            if (this->_identityToConnection.contains(address)) {
                conn = this->_identityToConnection[address].get();
            } else {
                const auto it = std::ranges::find(
                    _unestablishedConnection, address, &MessageConnectionTCP::_remoteIOSocketIdentity);
                if (it != _unestablishedConnection.end()) {
                    conn = it->get();
                } else {
                    onConnectionCreated(address);
                    conn = _unestablishedConnection.back().get();
                }
            }
            conn->sendMessage(std::move(message), std::move(callback));
        });
}

void IOSocket::recvMessage(RecvMessageCallback onRecvMessage) noexcept
{
    _eventLoopThread->_eventLoop.executeNow([this, callback = std::move(onRecvMessage)] mutable {
        if (_stopped) {
            callback({{}, Error::ErrorCode::IOSocketStopRequested});
            return;
        }

        if (_connectorDisconnected) {
            callback({{}, Error::ErrorCode::ConnectorSocketClosedByRemoteEnd});
            return;
        }

        this->_pendingRecvMessages->emplace(std::move(callback));
        if (_pendingRecvMessages->size() == 1) {
            for (const auto& [fd, conn]: _identityToConnection) {
                if (conn->recvMessage())
                    return;
            }
        }
    });
}

void IOSocket::connectTo(sockaddr addr, ConnectReturnCallback onConnectReturn, size_t maxRetryTimes) noexcept
{
    _eventLoopThread->_eventLoop.executeNow(
        [this, addr = std::move(addr), callback = std::move(onConnectReturn), maxRetryTimes] mutable {
            if (_tcpClient) {
                unrecoverableError({
                    Error::ErrorCode::MultipleConnectToNotSupported,
                    "Originated from",
                    "IOSocket::connectTo",
                });
            }

            _tcpClient.emplace(_eventLoopThread, this->identity(), std::move(addr), std::move(callback), maxRetryTimes);
            _tcpClient->onCreated();
        });
}

void IOSocket::connectTo(
    std::string networkAddress, ConnectReturnCallback onConnectReturn, size_t maxRetryTimes) noexcept
{
    auto res = stringToSockaddr(std::move(networkAddress));
    connectTo(std::move(res.value()), std::move(onConnectReturn), maxRetryTimes);
}

void IOSocket::bindTo(std::string networkAddress, BindReturnCallback onBindReturn) noexcept
{
    _eventLoopThread->_eventLoop.executeNow(
        [this, networkAddress = std::move(networkAddress), callback = std::move(onBindReturn)] mutable {
            if (_tcpServer) {
                callback(std::unexpected {Error::ErrorCode::MultipleBindToNotSupported});
                return;
            }
            auto res = stringToSockaddr(std::move(networkAddress));
            assert(res);

            _tcpServer.emplace(_eventLoopThread, this->identity(), std::move(res.value()), std::move(callback));
            _tcpServer->onCreated();
        });
}

void IOSocket::closeConnection(Identity remoteSocketIdentity) noexcept
{
    _eventLoopThread->_eventLoop.executeNow([this, remoteIdentity = std::move(remoteSocketIdentity)] {
        if (_stopped) {
            return;
        }
        if (_identityToConnection.contains(remoteIdentity))
            _identityToConnection[remoteIdentity]->disconnect();
    });
}

// TODO: The function should be separated into onConnectionAborted, onConnectionDisconnected,
// and probably onConnectionAbortedBeforeEstablished(?)
void IOSocket::onConnectionDisconnected(MessageConnectionTCP* conn, bool keepInBook) noexcept
{
    if (!conn->_remoteIOSocketIdentity) {
        return;
    }

    auto connIt = this->_identityToConnection.find(*conn->_remoteIOSocketIdentity);

    _unestablishedConnection.push_back(std::move(connIt->second));
    this->_identityToConnection.erase(connIt);
    auto& connPtr = _unestablishedConnection.back();

    if (!keepInBook) {
        if (IOSocketType::Connector == this->_socketType) {
            _connectorDisconnected = true;
            while (this->_pendingRecvMessages->size()) {
                auto top = std::move(this->_pendingRecvMessages->front());
                top({Message {}, {Error::ErrorCode::ConnectorSocketClosedByRemoteEnd}});
                this->_pendingRecvMessages->pop();
            }
        }
        _eventLoopThread->_eventLoop.executeLater([conn = std::move(connPtr)]() {});
        _unestablishedConnection.pop_back();
        return;
    }

    if (socketType() == IOSocketType::Unicast || socketType() == IOSocketType::Multicast) {
        auto destructWriteOp = std::move(connPtr->_writeOperations);
        connPtr->_writeOperations.clear();
        while (_pendingRecvMessages->size()) {
            _pendingRecvMessages->front()(
                {{}, Error::ErrorCode::RemoteEndDisconnectedOnSocketWithoutGuaranteedDelivery});
            _pendingRecvMessages->pop();
        }
        auto destructReadOp = std::move(connPtr->_receivedReadOperations);
    }

    if (connPtr->_responsibleForRetry) {
        connectTo(connPtr->_remoteAddr, [](auto) {});  // as the user callback is one-shot
    }
}

// FIXME: This algorithm runs in O(n) complexity. To reduce the complexity of this algorithm
// to O(lg n), one has to restructure how connections are placed. We would have three lists:
// - _unconnectedConnections that holds connections with identity but not fd
// - _unestablishedConnections that holds connections with fd but not identity
// - _connectingConnections that holds connections with fd and identity
// And this three lists shall be lookedup in above order based on this rule:
// - look up in _unestablishedConnections and move this connection to  _connectingConnections
// - look up _unconnectedConnections to find if there's a connection with the same identity
//   if so, merge it to this connection that currently resides in _connectingConnections
// Similar thing for disconnection as well.
void IOSocket::onConnectionIdentityReceived(MessageConnectionTCP* conn) noexcept
{
    auto& s = conn->_remoteIOSocketIdentity;
    if (socketType() == IOSocketType::Connector) {
        s = "";
    }

    auto thisConn = std::find_if(_unestablishedConnection.begin(), _unestablishedConnection.end(), [&](const auto& x) {
        return x.get() == conn;
    });
    _identityToConnection[*s] = std::move(*thisConn);
    _unestablishedConnection.erase(thisConn);

    auto rge = _unestablishedConnection                                                                        //
               | std::views::filter([](const auto& x) { return x->_remoteIOSocketIdentity != std::nullopt; })  //
               | std::views::filter([&s](const auto& x) { return *x->_remoteIOSocketIdentity == *s; })         //
               | std::views::take(1);
    if (rge.empty()) {
        return;
    }

    auto& targetConn = _identityToConnection[*s];

    auto c = _unestablishedConnection.begin() + (_unestablishedConnection.size() - rge.begin().count());

    while ((*c)->_writeOperations.size()) {
        targetConn->_writeOperations.emplace_back(std::move((*c)->_writeOperations.front()));
        (*c)->_writeOperations.pop_front();
    }

    targetConn->_pendingRecvMessageCallbacks = std::move((*c)->_pendingRecvMessageCallbacks);

    assert(targetConn->_receivedReadOperations.empty());
    targetConn->_receivedReadOperations = std::move((*c)->_receivedReadOperations);

    assert((*c)->_connFd == 0);
    _unestablishedConnection.erase(c);
}

void IOSocket::onConnectionCreated(std::string remoteIOSocketIdentity) noexcept
{
    _unestablishedConnection.push_back(
        std::make_unique<MessageConnectionTCP>(
            _eventLoopThread, this->identity(), std::move(remoteIOSocketIdentity), _pendingRecvMessages));
    _unestablishedConnection.back()->onCreated();
}

void IOSocket::onConnectionCreated(int fd, sockaddr localAddr, sockaddr remoteAddr, bool responsibleForRetry) noexcept
{
    _unestablishedConnection.push_back(
        std::make_unique<MessageConnectionTCP>(
            _eventLoopThread,
            fd,
            std::move(localAddr),
            std::move(remoteAddr),
            this->identity(),
            responsibleForRetry,
            _pendingRecvMessages));
    _unestablishedConnection.back()->onCreated();
}

void IOSocket::removeConnectedTcpClient() noexcept
{
    if (this->_tcpClient && this->_tcpClient->_connected) {
        this->_tcpClient.reset();
    }
}

void IOSocket::requestStop() noexcept
{
    _stopped = true;
    while (_pendingRecvMessages->size()) {
        auto readOp = std::move(_pendingRecvMessages->front());
        _pendingRecvMessages->pop();
        readOp({{}, Error::ErrorCode::IOSocketStopRequested});
    }
}

IOSocket::~IOSocket() noexcept
{
    while (_pendingRecvMessages->size()) {
        auto readOp = std::move(_pendingRecvMessages->front());
        _pendingRecvMessages->pop();
        readOp({{}, Error::ErrorCode::IOSocketStopRequested});
    }
}

}  // namespace ymq
}  // namespace scaler
