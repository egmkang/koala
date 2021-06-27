﻿using Gateway.Utils;
using Microsoft.AspNetCore.Connections;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Concurrent;
using System.Net;
using System.Threading.Tasks;

namespace Gateway.Network
{
    public class ClientConnectionPool
    {
        private readonly ILogger logger;
        private readonly IMessageCenter messageCenter;
        private readonly IConnectionFactory connectionFactory;
        private readonly SessionManager sessionManager;
        private readonly ConcurrentDictionary<long, WeakReference<ISession>> clients = new ConcurrentDictionary<long, WeakReference<ISession>>(4, 1024);
        private readonly LRU<long, object> recentRemoveServer = new LRU<long, object>(1024);

        public int AutoReconnectInterval { get; set; } = 5000;
        public int HeartBeatInterval { get; set; } = 5000;
        public long HeartBeatTimeOut { get; set; } = 5000 * 3;


        public ClientConnectionPool(ILoggerFactory loggerFactory, 
                                    IMessageCenter messageCenter, 
                                    IConnectionFactory connectionFactory,
                                    SessionManager sessionManager)
        {
            this.logger = loggerFactory.CreateLogger("Network");
            this.messageCenter = messageCenter;
            this.connectionFactory = connectionFactory;
            this.sessionManager = sessionManager;
        }

        public void OnAddServer(long serverID, EndPoint endPoint, Func<object> heartbeatMessageFn) 
        {
            _ = this.ReconnectLoop(serverID, endPoint, heartbeatMessageFn);
        }

        private static readonly object Empty = new object();
        public void OnRemoveServer(long serverID) 
        {
            this.recentRemoveServer.Add(serverID, Empty);
            this.TryCloseCurrentClient(serverID);
        }

        public ISession GetSession(long serverID) 
        {
            if (this.clients.TryGetValue(serverID, out var weakSession) && weakSession.TryGetTarget(out var session))
            {
                return session;
            }
            return null;
        }

        private async Task ReconnectLoop(long serverID, EndPoint endPoint, Func<object> heartbeatMessageFn) 
        {
            while (true)
            {
                if (this.recentRemoveServer.Get(serverID) != null)
                {
                    this.logger.LogInformation("ExitReconnectLoop, ServerID:{0}", serverID);
                    return;
                }

                if (this.GetSession(serverID) == null)
                {
                    await this.TryConnectAsync(serverID, endPoint, heartbeatMessageFn).ConfigureAwait(false);
                }

                await Task.Delay(AutoReconnectInterval).ConfigureAwait(false);
            }
        }

        private void TryCloseCurrentClient(long serverID) 
        {
            try
            {
                if (this.clients.TryGetValue(serverID, out var c) && c.TryGetTarget(out var session))
                {
                    this.logger.LogInformation("TryCloseCurrentClient, ServerID:{1} SessionID:{0}",
                        session.UserData.SessionID, serverID);
                    _ = session.CloseAsync();

                    this.clients.TryRemove(serverID, out var _);
                }
                else
                {
                    this.logger.LogInformation("TryCloseCurrentClient, cannot find ServerID:{0}", serverID);
                }
            }
            catch (Exception e)
            {
                logger.LogError("TryCloseCurrentClient, Exception:{0}", e.Message);
            }
        }


        private async Task TrySendHeartBeatLoop(TcpSocketSession session, Func<object> heartbeatMessageFn)
        {
            if (heartbeatMessageFn == null) return;

            var sessionInfo = session.UserData;

            while (session.IsActive)
            {
                //this.logger.LogTrace("TrySendHeartBeat, SessionID:{0}", sessionInfo.SessionID);
                try
                {
                    if (Platform.GetMilliSeconds() - session.LastMessageTime > HeartBeatTimeOut)
                    {
                        this.logger.LogError("HearBeatTimeOut, SessionID:{0}, ServerID:{1}, RemoteAddress:{2}, TimeOut:{3}",
                            sessionInfo.SessionID, sessionInfo.GameServerID, session.RemoteAddress, Platform.GetMilliSeconds() - session.LastMessageTime);

                        this.TryCloseCurrentClient(sessionInfo.GameServerID);
                        break;
                    }

                    await session.SendMessage(heartbeatMessageFn()).ConfigureAwait(false);
                }
                catch (Exception e)
                {
                    this.logger.LogError("TrySendHeartBeatLoop, SessionID:{0}, Exception:{1}",
                        sessionInfo.SessionID, e);
                }

                await Task.Delay(HeartBeatInterval).ConfigureAwait(false);
            }
            this.logger.LogInformation("TrySednHeartBeatLoop Exit, SessionID:{0}", sessionInfo.SessionID);

        }

        private TcpSocketSession NewTcpClientSession(ConnectionContext connection, long serverID) 
        {
            var sessionID = this.sessionManager.NewSessionID;
            var sessionInfo = new DefaultSessionInfo(sessionID, serverID);
            var session = new TcpSocketSession(sessionID, connection, sessionInfo);

            this.sessionManager.AddSession(session);
            return session;
        }

        private async Task TryConnectAsync(long serverID, EndPoint endPoint, Func<object> heartbeatMessageFn) 
        {
            try
            {
                if (this.recentRemoveServer.Get(serverID) != null)
                {
                    this.logger.LogInformation("TryConnectAsync, ServerID:{0} has been canceled", serverID);
                    return;
                }
                this.logger.LogInformation("TryConnectAsync, ServerID:{0}, Address:{1} Start", serverID, endPoint);

                var connection = await this.connectionFactory.ConnectAsync(endPoint).ConfigureAwait(false);
                var session = this.NewTcpClientSession(connection, serverID);

                this.logger.LogInformation("TryConnectAsync, ServerID:{0}, Address:{1}, SessionID:{2}",
                    serverID, endPoint, session.SessionID);

                var weak = new WeakReference<ISession>(session);
                this.clients.AddOrUpdate(serverID, weak, (_1, _2) => weak);

                _ = session.RecvLoop();
                _ = this.TrySendHeartBeatLoop(session, heartbeatMessageFn);
            }
            catch (Exception e)
            {
                this.logger.LogError("TryConnectAsync, ServerID:{0}, Address:{1}, Exception:{2}",
                    serverID, endPoint, e.Message);
            }
        }
    }
}
