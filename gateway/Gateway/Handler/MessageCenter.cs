using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Gateway.Message;
using Gateway.Placement;
using Gateway.Network;
using Abstractions.Placement;

namespace Gateway.Handler
{
    public class MessageCenter : IMessageCenter
    {
        private readonly IServiceProvider serviceProvider;
        private readonly ILogger logger;
        private readonly SessionManager sessionManager;
        private readonly ClientConnectionPool clientConnectionPool;
        private MessageCallback defaultHandler;
        private readonly Dictionary<Type, MessageCallback> messageHandlers = new Dictionary<Type, MessageCallback>();

        public MessageCenter(IServiceProvider serviceProvider, 
                            SessionManager sessionManager, 
                            ILoggerFactory loggerFactory, 
                            IPlacement placement,
                            ClientConnectionPool clientConnectionPool) 
        {
            this.serviceProvider = serviceProvider;
            this.sessionManager = sessionManager;
            this.clientConnectionPool = clientConnectionPool;
            this.logger = loggerFactory.CreateLogger("MessageCenter");
        }

        private WebSocketClose WebSocketClose { get; set; }
        private WebSocketMessage WebSocketMessage { get; set; }


        public Task OnSocketClose(ISession session)
        {
            this.sessionManager.RemoveSession(session.SessionID);
            this.logger.LogWarning("MessageCenter OnSocketClose, SessionID:{0}", session.SessionID);
            return Task.CompletedTask;
        }

        public async Task OnSocketMessage(ISession session, RpcMeta rpcMeta, byte[] body)
        {
            try
            {
                if (this.messageHandlers.TryGetValue(rpcMeta.GetType(), out var handler))
                {
                    await handler(session, rpcMeta, body).ConfigureAwait(false);
                }
                else 
                {
                    await defaultHandler(session, rpcMeta, body).ConfigureAwait(false);
                }
            }
            catch (Exception e)
            {
                this.logger.LogError("MessageCenter OnSocketMessage, SessionID:{0} Exception:{1}", session.SessionID, e);
            }
        }

        public Task OnWebSocketClose(ISession session)
        {
            return this.WebSocketClose(session);
        }

        public Task OnWebSocketMessage(ISession session, Memory<byte> memory, int size)
        {
            return this.WebSocketMessage(session, memory, size);
        }

        public async Task SendMessageToServer(long serverID, object msg)
        {
            var session = this.clientConnectionPool.GetSession(serverID);
            if (session == null) 
            {
                this.logger.LogWarning("SendMessageToServer, SeverID:{0} not found", serverID);
                return;
            }
            await session.SendMessage(msg).ConfigureAwait(false);
        }

        public async Task SendMessageToSession(long sessionID, object msg)
        {
            var session = this.sessionManager.GetSession(sessionID);
            if (session == null) 
            {
                this.logger.LogWarning("SendMessageToSession, SessionID:{0} not found", sessionID);
                return;
            }
            await session.SendMessage(msg).ConfigureAwait(false);
        }

        public void RegisterMessageCallback(Type type, MessageCallback handler)
        {
            if (type == null)
            {
                this.defaultHandler = handler;
            }
            else 
            {
                this.messageHandlers.Add(type, handler);
            }
        }

        public void RegisterWebSocketCallback(WebSocketMessage messageCallback, WebSocketClose closeCallback)
        {
            this.WebSocketMessage = messageCallback;
            this.WebSocketClose = closeCallback;
        }
    }
}
