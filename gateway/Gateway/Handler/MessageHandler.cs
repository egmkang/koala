using System;
using System.Collections.Generic;
using System.Linq;
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
                                        sessionInfo.SessionID, sessionInfo.ActorType, sessionInfo.ActorID);

            var position = await this.placement.FindActorPositonAsync(new PlacementFindActorPositionRequest()
            {
                ActorType = sessionInfo.ActorType,
                ActorID = sessionInfo.ActorID,
            }).ConfigureAwait(false);

            sessionInfo.DestServerID = position.ServerID;
            this.logger.LogInformation("ProcessResponseQueryAccount, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                                        sessionInfo.SessionID, sessionInfo.ActorType, sessionInfo.ActorID, sessionInfo.DestServerID);
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
    }
}
