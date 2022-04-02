using System;
using System.Net;
using Microsoft.Extensions.Logging;
using Abstractions.Network;
using Abstractions.Placement;
using Gateway.Network;
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

            this.placement.RegisterServerChangedEvent(this.OnAddServer, this.OnRemoveServer, this.OnOfflineServer);
            this.placement.OnException(this.OnPDKeepAliveException);
        }

        private void OnPDKeepAliveException(Exception e) 
        {
            this.logger.LogError("PDKeepAlive, Exception:{0}", e);
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
    }
}
