using System;
using System.Net;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using DotNetty.Transport.Channels;
using Gateway.Utils;
using Abstractions.Network;

namespace Gateway.Network
{
    internal class ClientConnectionPool
    {
        private readonly ILogger logger;
        private readonly IClientConnectionFactory connectionFactory;
        //ServerID => IChannel
        private readonly ConcurrentDictionary<long, WeakReference<IChannel>> clients = new ConcurrentDictionary<long, WeakReference<IChannel>>();
        private readonly LRU<long, object> recentRemoveServer = new LRU<long, object>(1024);

        public int AutoReconnectInterval { get; set; } = 5000;
        public int HeartBeatInterval { get; set; } = 5000;
        public long HeartBeatTimeOut { get; set; } = 5000 * 3;

        public ClientConnectionPool(ILoggerFactory loggerFactory,
            IClientConnectionFactory clientConnectionFactory)
        {
            this.logger = loggerFactory.CreateLogger("Network");
            this.connectionFactory = clientConnectionFactory;
        }

        public IMessageHandlerFactory MessageHandlerFactory { get; set; }

        public void OnAddServer(long serverID, EndPoint endPoint, Func<object> heartBeatMessageFn) 
        {
            _ = this.ReconnectLoop(serverID, endPoint, heartBeatMessageFn);
        }

        private static readonly object empty = new object();
        public void OnRemoveServer(long serverID) 
        {
            this.recentRemoveServer.Add(serverID, empty);
            this.TryCloseCurrentClient(serverID);
        }

        public IChannel GetChannelByServerID(long serverID) 
        {
            if (this.clients.TryGetValue(serverID, out var c) && c.TryGetTarget(out var channel))
            {
                return channel;
            }
            return null;
        }

        private async Task ReconnectLoop(long serverID, EndPoint endPoint, 
                                         Func<object> heartBeatMessageFn) 
        {
            while (true) 
            {
                if (this.recentRemoveServer.Get(serverID) != null) 
                {
                    this.logger.LogInformation("ExitReconnectLoop, ServerID:{0}", serverID);
                    return;
                }

                if (this.GetChannelByServerID(serverID) == null) 
                {
                    await this.TryConnectAsync(serverID, endPoint, heartBeatMessageFn).ConfigureAwait(false);
                }

                await Task.Delay(AutoReconnectInterval).ConfigureAwait(false);
            }
        }

        private async Task TryConnectAsync(long serverID, EndPoint endPoint, 
                                            Func<object> heartBeatMessageFn)
        {
            try
            {
                if (this.recentRemoveServer.Get(serverID) != null)
                {
                    this.logger.LogInformation("TryConnectAsync, ServerID:{0} has been canceled", serverID);
                    return;
                }
                this.logger.LogInformation("TryConnectAsync, ServerID:{0}, Address:{1} Start", serverID, endPoint);

                var channel = await this.connectionFactory.ConnectAsync(endPoint, this.MessageHandlerFactory).ConfigureAwait(false);
                var sessionInfo = channel.GetSessionInfo();
                this.logger.LogInformation("TryConnectAsync, ServerID:{0}, Address:{1}, SessionID:{2}",
                    serverID, endPoint, sessionInfo.SessionID);

                sessionInfo.ServerID = serverID;
                var weak = new WeakReference<IChannel>(channel);
                this.clients.AddOrUpdate(serverID, weak, (_1, _2) => weak);

                _ = this.TrySendHeartBeatLoop(channel, heartBeatMessageFn);
            }
            catch (Exception e) 
            {
                this.logger.LogError("TryConnectAsync, ServerID:{0}, Address:{1}, Exception:{2}",
                    serverID, endPoint, e.Message);
            }
        }
        private async Task TrySendHeartBeatLoop(IChannel channel, Func<object> heartBeatMessageFn)
        {
            if (heartBeatMessageFn == null) return;

            var sessionInfo = channel.GetSessionInfo();

            while (sessionInfo.IsActive)
            {
                //this.logger.LogTrace("TrySendHeartBeat, SessionID:{0}", sessionInfo.SessionID);
                try
                {
                    if (Platform.GetMilliSeconds() - sessionInfo.ActiveTime > HeartBeatTimeOut)
                    {
                        this.logger.LogError("HearBeatTimeOut, SessionID:{0}, ServerID:{1}, RemoteAddress:{2}, TimeOut:{3}",
                            sessionInfo.SessionID, sessionInfo.ServerID, sessionInfo.RemoteAddress, Platform.GetMilliSeconds() - sessionInfo.ActiveTime);

                        this.TryCloseCurrentClient(sessionInfo.ServerID);
                        break;
                    }

                    var msg = new OutboundMessage(channel, heartBeatMessageFn());
                    sessionInfo.PutOutboundMessage(msg);
                }
                catch (Exception e)
                {
                    this.logger.LogError("TrySendHeartBeatLoop, SessionID:{0}, Exception:{1}",
                        sessionInfo.SessionID, e);
                }

                await Task.Delay(HeartBeatInterval).ConfigureAwait(false);
            }
            this.logger.LogInformation("TrySendHeartBeatLoop Exit, SessionID:{0}", sessionInfo.SessionID);
        }

        private void TryCloseCurrentClient(long serverID) 
        {
            try
            {
                if (this.clients.TryGetValue(serverID, out var c) && c.TryGetTarget(out var channel))
                {
                    this.logger.LogInformation("TryCloseCurrentClient, ServerID:{1} SessionID:{0}",
                        channel.GetSessionInfo().SessionID, serverID);
                    channel.CloseAsync();

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
    }
}
