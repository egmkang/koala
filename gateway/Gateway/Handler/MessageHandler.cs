using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Gateway.Message;
using Gateway.Network;
using Gateway.Placement;
using Gateway.Utils;
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
        private readonly ClientMessageCodec codec = new ClientMessageCodec();

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

            this.messageCenter.RegisterWebSocketCallback(this.ProcessWebSocketMessage, this.ProcessWebSocketClose);

            this.messageCenter.RegisterMessageCallback(null, this.ProcessDefaultMessage);
            this.RegisterHandler<ResponseAccountLogin>(this.ProcessResponseAccountLogin);
            this.RegisterHandler<RequestCloseSession>(this.ProcessRequestCloseSession);
            this.RegisterHandler<RequestSendMessageToSession>(this.ProcessRequestSendMessageToSession);
            this.RegisterHandler<RequestHeartBeat>(this.ProcessRequestHeartBeat);
            this.RegisterHandler<ResponseHeartBeat>(this.ProcessResponseHeartBeat);
        }
        private void RegisterHandler<T>(Func<ISession, T, byte[], Task> func) where T : RpcMeta
        {
            MessageCallback f = (session, msg, body) => func(session, msg as T, body);
            this.messageCenter.RegisterMessageCallback(typeof(T), f);
            this.logger.LogInformation("RegisterHandler, Type:{0}", typeof(T).Name);
        }

        private Task ProcessDefaultMessage(ISession session, RpcMeta rpcMeta, byte[] body) 
        {
            this.logger.LogWarning("ProcessDefaultMessage, SessionID:{0} MessageType:{1}", session.SessionID, rpcMeta?.GetType().Name);
            return Task.CompletedTask;
        }

        private async Task ProcessResponseAccountLogin(ISession session, ResponseAccountLogin response, byte[] body) 
        {
            var destSession = this.sessionManager.GetSession(response.SessionID);
            if (destSession == null) 
            {
                this.logger.LogInformation("ProcessResponseQueryAccount Session Not Found,SessionID:{0}", response.SessionID);
                return;
            }

            var sessionInfo = destSession.UserData;
            sessionInfo.ActorType = response.ActorType;
            sessionInfo.ActorID = response.ActorID;
            this.logger.LogInformation("ProcessResponseQueryAccount, SessionID:{0}, OpenID:{1}, Actor:{2}/{3}",
                                        sessionInfo.SessionID, sessionInfo.OpenID, sessionInfo.ActorType, sessionInfo.ActorID);

            var position = await this.FindActorPositionAsync(sessionInfo.ActorType, sessionInfo.ActorID).ConfigureAwait(false);
            if (sessionInfo.DestServerID != position.ServerID) 
            {
                sessionInfo.DestServerID = position.ServerID;
                this.logger.LogInformation("ProcessResponseQueryAccount, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                                            sessionInfo.SessionID, sessionInfo.ActorType,
                                            sessionInfo.ActorID, sessionInfo.DestServerID);
            }

            await this.messageCenter.SendMessageToServer(sessionInfo.DestServerID, new RpcMessage(new NotifyNewActorSession()
            {
                SessionID = sessionInfo.SessionID,
                OpenID = sessionInfo.OpenID,
                ServerID = sessionInfo.GameServerID,
                ActorType = sessionInfo.ActorType,
                ActorID = sessionInfo.ActorID,
            }, sessionInfo.Token)).ConfigureAwait(false);
        }
        private async Task ProcessRequestCloseSession(ISession session, RequestCloseSession request, byte[] body) 
        {
            var closeSession = this.sessionManager.GetSession(request.SessionID);
            if (closeSession != null) 
            {
                this.logger.LogInformation("ProcessRequestCloseConnection, SessionID:{0}", request.SessionID);
                await closeSession.CloseAsync().ConfigureAwait(false);
            }
        }
        private async Task ProcessRequestSendMessageToSession(ISession session, RequestSendMessageToSession request, byte[] body) 
        {
            if (request.SessionId != 0) 
            {
                await this.messageCenter.SendMessageToSession(request.SessionId, body).ConfigureAwait(false);
            }
            else 
            {
                foreach (var sessionID in request.SessionIds)
                {
                    await this.messageCenter.SendMessageToSession(sessionID, body).ConfigureAwait(false);
                }
            }
        }
        private async Task ProcessRequestHeartBeat(ISession session, RequestHeartBeat request, byte[] body) 
        {
            var response = new ResponseHeartBeat() { MilliSeconds = request.MilliSeconds, };
            await session.SendMessage(new RpcMessage(response, null)).ConfigureAwait(false);
        }
        private Task ProcessResponseHeartBeat(ISession session, ResponseHeartBeat response, byte[] body) 
        {
            var costTime = Platform.GetMilliSeconds() - response.MilliSeconds;
            if (costTime > 50)
            {
                this.logger.LogWarning("ProcessResponseHeartBeat, SessionID:{0} CostTime:{1}", session.SessionID, costTime);
            }
            session.LastMessageTime = Platform.GetMilliSeconds();
            return Task.CompletedTask;
        }
        private async Task ProcessWebSocketMessage(ISession session, Memory<byte> memory, int size) 
        {
            var sessionInfo = session.UserData;
            if (sessionInfo.GameServerID != 0)
            {
                await this.ProcessWebSocketCommonMessage(session, memory, size).ConfigureAwait(false);
            }
            else
            {
                await this.ProcessWebSocketFirstMessage(session, memory, size).ConfigureAwait(false);
            }
        }

        static readonly Random random = new Random();
        private static int RandomLoginServer => random.Next(0, 1024 * 10);
        public static readonly string AccountService = "IAccount";
        private static ThreadLocal<PlacementFindActorPositionRequest> findActorRequestCache = new ThreadLocal<PlacementFindActorPositionRequest>(() => new PlacementFindActorPositionRequest());

        private async Task<PlacementFindActorPositionResponse> FindActorPositionAsync(string actorType, string actorID) 
        {
            var findPositionReq = findActorRequestCache.Value;
            findPositionReq.ActorType = actorType;
            findPositionReq.ActorID = actorID;
            var position = await this.placement.FindActorPositonAsync(findPositionReq).ConfigureAwait(false);
            return position;
        }

        private async Task ProcessWebSocketFirstMessage(ISession session, Memory<byte> memory, int size)
        {
            // TODO
            //这边还要处理断线重来
            var sessionInfo = session.UserData;
            var (OpenID, ServerID) = this.codec.Decode(memory, size);
            this.logger.LogInformation("WebSocketSession Login, SessionID:{0}, OpenID:{1}, ServerID:{2}",
                                        sessionInfo.SessionID, OpenID, ServerID);
            sessionInfo.OpenID = OpenID;
            sessionInfo.GameServerID = ServerID;

            var body = new byte[size];
            memory.Span.Slice(0, size).CopyTo(body);
            sessionInfo.Token = body;

            //这边需要通过账号信息, 查找目标Actor的位置
            var position =  await this.FindActorPositionAsync(AccountService, RandomLoginServer.ToString()).ConfigureAwait(false);

            var req = new RpcMessage(new RequestAccountLogin()
            {
                OpenID = sessionInfo.OpenID,
                ServerID = sessionInfo.GameServerID,
                SessionID = session.SessionID,
            }, body);
            await this.messageCenter.SendMessageToServer(position.ServerID, req).ConfigureAwait(false);
        }
        private async Task ProcessWebSocketCommonMessage(ISession session, Memory<byte> memory, int size) 
        {
            var sessionInfo = session.UserData;
            if (string.IsNullOrEmpty(sessionInfo.ActorType)) 
            {
                this.logger.LogError("WebSocketSession Invalid Dest Server, SessionID:{0}", session.SessionID);
                return;
            }

            var position = await this.FindActorPositionAsync(sessionInfo.ActorType, sessionInfo.ActorID).ConfigureAwait(false);
            if (sessionInfo.DestServerID != position.ServerID) 
            {
                sessionInfo.DestServerID = position.ServerID;
                this.logger.LogInformation("WebSocketSession, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                                            session.SessionID, sessionInfo.ActorType, sessionInfo.ActorID,
                                            sessionInfo.DestServerID);
            }

            var body = new byte[size];
            memory.Span.Slice(0, size).CopyTo(body);
            await this.messageCenter.SendMessageToServer(sessionInfo.DestServerID, new RpcMessage(new NotifyNewActorMessage()
            {
                ActorType = sessionInfo.ActorType,
                ActorID = sessionInfo.ActorID,
                SessionId = session.SessionID,
            }, body)).ConfigureAwait(false);
        }
        private async Task ProcessWebSocketClose(ISession session)
        {
            try
            {
                if (!session.IsActive)
                    return;
                var sessionInfo = session.UserData;
                var position = await this.FindActorPositionAsync(sessionInfo.ActorType, sessionInfo.ActorID).ConfigureAwait(false);

                var closeMessage = new RpcMessage(new NotifyActorSessionAborted()
                {
                    SessionID = session.SessionID,
                    ActorType = sessionInfo.ActorType,
                    ActorID = sessionInfo.ActorID,
                }, null);

                await this.messageCenter.SendMessageToServer(position.ServerID, closeMessage).ConfigureAwait(false);
                this.logger.LogInformation("WebSocketSession OnClose, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                    session.SessionID, sessionInfo.ActorType, sessionInfo.ActorID, position.ServerID);
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
    }
}
