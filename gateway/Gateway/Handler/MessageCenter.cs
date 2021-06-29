using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Gateway.Message;
using Gateway.Placement;
using Gateway.Network;

namespace Gateway.Handler
{
    public class MessageCenter : IMessageCenter
    {
        private readonly IServiceProvider serviceProvider;
        private readonly ILogger logger;
        private readonly SessionManager sessionManager;
        private readonly IPlacement placement;
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
            this.placement = placement;
            this.clientConnectionPool = clientConnectionPool;
            this.logger = loggerFactory.CreateLogger("MessageCenter");
        }

        public Task OnSocketClose(ISession session)
        {
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

        public async Task OnWebSocketClose(ISession session)
        {
            try 
            {
                var sessionInfo = session.UserData;
                if (sessionInfo.DestServerID != 0)
                {
                    var closeMessage = new RpcMessage(new NotifyConnectionAborted()
                    {
                        SessionId = session.SessionID,
                        ServiceType = sessionInfo.ActorType,
                        ActorId = sessionInfo.ActorID,
                    }, null);

                    await this.SendMessageToServer(sessionInfo.DestServerID, closeMessage).ConfigureAwait(false);
                    this.logger.LogInformation("WebSocketSession OnClose, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                        session.SessionID, sessionInfo.ActorType, sessionInfo.ActorID, sessionInfo.DestServerID);
                }
                else 
                {
                    this.logger.LogInformation("WebSocketSession OnClose, SessionID:{0}, DestServerID: 0", session.SessionID);
                }
            }
            catch (Exception e) 
            {
                this.logger.LogError("WebSocketSession OnClose, SessionID:{0}, Exception:{1}", session.SessionID, e);
            }
            finally 
            {
                this.sessionManager.RemoveSession(session.SessionID);
            }
        }

        static readonly Random random = new Random();
        private static int RandomLoginServer => random.Next(0, 1024 * 10);
        public static readonly string AccountService = "IAccount";

        public async Task OnWebSocketLoginMessage(ISession session, string openID, int serverID, Memory<byte> memory, int size)
        {
            var body = new byte[size];
            memory.CopyTo(body);
            //这边需要通过账号信息, 查找目标Actor的位置
            var sessionInfo = session.UserData;
            sessionInfo.OpenID = openID;
            sessionInfo.GameServerID = serverID;
            sessionInfo.Token = body;

            var position = await this.placement.FindActorPositonAsync(new PlacementFindActorPositionRequest()
            {
                ActorType = AccountService,
                ActorID = RandomLoginServer.ToString(),
            }).ConfigureAwait(false);

            var req = new RpcMessage(new RequestQueryAccount()
            {
                OpenID = sessionInfo.OpenID,
                ServerID = sessionInfo.GameServerID,
                SessionID = session.SessionID,
            }, body);
            await this.SendMessageToServer(position.ServerID, req).ConfigureAwait(false);
        }

        public async Task OnWebSocketMessage(ISession session, Memory<byte> memory, int size)
        {
            var sessionInfo = session.UserData;
            if (string.IsNullOrEmpty(sessionInfo.ActorType)) 
            {
                this.logger.LogError("WebSocketSession Invalid Dest Server, SessionID:{0}", session.SessionID);
                return;
            }
            if (sessionInfo.DestServerID == 0)
            {
                var req = new PlacementFindActorPositionRequest()
                {
                    ActorType = sessionInfo.ActorType,
                    ActorID = sessionInfo.ActorID,
                };
                var position = await this.placement.FindActorPositonAsync(req).ConfigureAwait(false);

                sessionInfo.DestServerID = position.ServerID;
                this.logger.LogInformation("WebSocketSession, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                    session.SessionID, sessionInfo.ActorType, sessionInfo.ActorID, sessionInfo.DestServerID);
            }

            var body = new byte[size];
            memory.CopyTo(body);
            await this.SendMessageToServer(sessionInfo.DestServerID, new RpcMessage(new NotifyNewMessage()
            {
                ServiceType = sessionInfo.ActorType,
                ActorId = sessionInfo.ActorID,
                SessionId = session.SessionID,
            }, body)).ConfigureAwait(false);
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
    }
}
