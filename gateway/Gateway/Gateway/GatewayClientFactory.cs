using System;
using System.Net;
using Microsoft.Extensions.Logging;
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
    }
}
