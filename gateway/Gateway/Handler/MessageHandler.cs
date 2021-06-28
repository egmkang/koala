using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Gateway.Message;
using Gateway.Network;
using Gateway.Placement;
using Microsoft.Extensions.Logging;

namespace Gateway.Handler
{
    public class MessageHandler
    {
        private readonly IServiceProvider serviceProvider;
        private readonly ILogger logger;
        private readonly SessionManager sessionManager;
        private readonly IPlacement placement;
        private readonly ClientConnectionPool clientConnectionPool;
        private readonly IMessageCenter messageCenter;
        public MessageHandler(IServiceProvider serviceProvider,
                                IMessageCenter messageCenter,
                                ILoggerFactory loggerFactory,
                                SessionManager sessionManager, 
                                IPlacement placement, 
                                ClientConnectionPool clientConnectionPool) 
        {
            this.serviceProvider = serviceProvider;
            this.logger = loggerFactory.CreateLogger("MessageHandler");
            this.messageCenter = messageCenter;
            this.sessionManager = sessionManager;
            this.placement = placement;
            this.clientConnectionPool = clientConnectionPool;

            this.RegisterHandler<ResponseQueryAccount>(this.ProcessResponseQueryAccount);
            this.RegisterHandler<RequestCloseConnection>(this.ProcessRequestCloseConnection);
            this.RegisterHandler<RequestSendMessageToPlayer>(this.ProcessRequestSendMessageToPlayer);
            this.RegisterHandler<HeartBeatRequest>(this.ProcessRequestHeartBeat);
            this.RegisterHandler<HeartBeatResponse>(this.ProcessResponseHeartBeat);
        }
        private void RegisterHandler<T>(Func<ISession, T, byte[], Task> func) where T : RpcMeta
        {
            MessageCallback f = (session, msg, body) => func(session, (T)msg, body);
            this.messageCenter.RegisterMessageHandler(typeof(T), f);
            this.logger.LogDebug("RegisterHandler, Type:{0}", typeof(T).Name);
        }

        private Task ProcessResponseQueryAccount(ISession session, ResponseQueryAccount response, byte[] body) 
        {
            return Task.CompletedTask;
        }
        private Task ProcessRequestCloseConnection(ISession session, RequestCloseConnection request, byte[] body) 
        {
            return Task.CompletedTask;
        }
        private Task ProcessRequestSendMessageToPlayer(ISession session, RequestSendMessageToPlayer request, byte[] body) 
        {
            return Task.CompletedTask;
        }
        private Task ProcessRequestHeartBeat(ISession session, HeartBeatRequest request, byte[] body) 
        {
            return Task.CompletedTask;
        }
        private Task ProcessResponseHeartBeat(ISession session, HeartBeatResponse response, byte[] body) 
        {
            return Task.CompletedTask;
        }
    }
}
