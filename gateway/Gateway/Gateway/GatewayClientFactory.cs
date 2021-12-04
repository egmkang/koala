using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Text;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using DotNetty.Transport.Channels;
using Abstractions.Network;
using Abstractions.Placement;
using Gateway.NetworkNetty;
using Gateway.Message;
using Gateway.Utils;

namespace Gateway.Gateway
{
    internal class GatewayClientFactory
    {
        private readonly IPlacement placement;
        private readonly IMessageCenter messageCenter;
        private readonly ILogger logger;
        private readonly ClientConnectionPool clientConnectionPool;

        public GatewayClientFactory(ILoggerFactory loggerFactory,
            IMessageCenter messageCenter,
            IPlacement placement,
            ClientConnectionPool clientPool
            )
        {
            this.logger = loggerFactory.CreateLogger("GatewayClient");
            this.messageCenter = messageCenter;
            this.placement = placement;
            this.clientConnectionPool = clientPool;

            //消息处理
            this.messageCenter.RegisterTypedMessageProc<ResponseHeartBeat>(this.ProcessHeartBeatResponse);
            this.messageCenter.RegisterTypedMessageProc<NotifyNewActorSession>(this.ProcessNotifyNewActorSession);
            this.messageCenter.RegisterTypedMessageProc<NotifyActorSessionAborted>(this.ProcessNotifyActorSessionAborted);
            this.messageCenter.RegisterTypedMessageProc<NotifyNewActorMessage>(this.ProcessNotifyNewActorMessage);
        }

        public void OnAddServer(PlacementActorHostInfo server)
        {
            Func<object> fn = () =>
            {
                var rpcMessage = new RpcMessage(new RequestHeartBeat() { MilliSeconds = Platform.GetMilliSeconds() }, null);
                return rpcMessage;
            };
            this.clientConnectionPool.OnAddServer(server.ServerID,
                                                IPEndPoint.Parse(server.Address), fn);
        }
        public void OnRemoveServer(PlacementActorHostInfo server)
        {
            this.clientConnectionPool.OnRemoveServer(server.ServerID);
        }
        public void OnOfflineServer(PlacementActorHostInfo server)
        {
            //TODO
            //貌似不需要干什么
        }

        private void ProcessHeartBeatResponse(InboundMessage message)
        {
            var msg = (message.Inner as RpcMessage).Meta as ResponseHeartBeat;
            if (msg == null)
            {
                this.logger.LogError("ProcessHeartBeat input message type:{0}", message.Inner?.GetType());
                return;
            }
            var elapsedTime = Platform.GetMilliSeconds() - msg.MilliSeconds;
            if (elapsedTime >= 5)
            {
                var sessionInfo = message.SourceConnection.GetSessionInfo();
                this.logger.LogWarning("ProcessHearBeat, SessionID:{0}, ServerID:{1}, RemoteAddress:{2}, Elapsed Time:{3}ms",
                    sessionInfo.SessionID, sessionInfo.ServerID, sessionInfo.RemoteAddress, elapsedTime);
            }
        }

        private void ProcessNotifyNewActorSession(InboundMessage message) 
        {
            var msg = (message.Inner as RpcMessage).Meta as NotifyNewActorSession;
            if (msg == null) 
            {
                this.logger.LogError("ProcessNotifyConnectionComing input message type:{0}", message.Inner?.GetType());
                return;
            }
            this.messageCenter.OnReceiveUserMessage(msg.ActorType, msg.ActorID, message);
        }

        private void ProcessNotifyActorSessionAborted(InboundMessage message)
        {
            var msg = (message.Inner as RpcMessage).Meta as NotifyActorSessionAborted;
            if (msg == null)
            {
                this.logger.LogError("ProcessNotifyConnectionAborted input message type:{0}", message.Inner?.GetType());
                return;
            }
            var actorID = msg.ActorID;
            if (string.IsNullOrEmpty(actorID)) 
            {
                this.logger.LogWarning("ProcessNotifyConnectionAborted, SessionID:{0}, ActorID not found", msg.SessionID);
                return;
            } 
            this.messageCenter.OnReceiveUserMessage(msg.ActorType, actorID, message);

            Task.Run(async () =>
            {
                //1分钟后GC掉SessionInfo
                await Task.Delay(60 * 1000).ConfigureAwait(false);
            });
        }

        private void ProcessNotifyNewActorMessage(InboundMessage message) 
        {
            var msg = (message.Inner as RpcMessage).Meta as NotifyNewActorMessage;
            if (msg == null) 
            {
                this.logger.LogError("ProcessNewMessage input message type:{0}", message.Inner?.GetType());
                return;
            }
            var actorID = msg.ActorID;
            if (string.IsNullOrEmpty(actorID)) 
            {
                this.logger.LogWarning("ProcessNewMessage, SessionID:{0}, ActorID not found", msg.SessionId);
                return;
            }
            if (msg.Trace.Length != 0) 
            {
                this.logger.LogWarning("PrcessNewMessage, SessionID:{0}, actorID:{1}, Trace:{2}",
                    msg.SessionId, actorID, msg.Trace);
            }
            this.messageCenter.OnReceiveUserMessage(msg.ActorType, actorID, message);
        }

    }
}
