using System;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Abstractions.Network;
using Abstractions.Placement;
using DotNetty.Transport.Channels;
using Gateway.Message;
using Gateway.Network;
using Gateway.Placement;
using Gateway.Utils;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace Gateway.Handler
{
    public class GatewayMessageHandler
    {
        private readonly IServiceProvider serviceProvider;
        private readonly ILogger logger;
        private readonly IConnectionManager sessionManager;
        private readonly IPlacement placement;
        private readonly ClientConnectionPool clientConnectionPool;
        private readonly IMessageCenter messageCenter;

        public GatewayMessageHandler(IServiceProvider serviceProvider,
                                IMessageCenter messageCenter,
                                ILoggerFactory loggerFactory,
                                IConnectionManager sessionManager,
                                IPlacement placement)

        {
            this.serviceProvider = serviceProvider;
            this.logger = loggerFactory.CreateLogger("MessageHandler");
            this.messageCenter = messageCenter;
            this.sessionManager = sessionManager;
            this.placement = placement;
            this.clientConnectionPool = serviceProvider.GetRequiredService<ClientConnectionPool>();

            this.messageCenter.RegisterMessageProc(new BlockMessageCodec().CodecName, this.ProcessWebSocketMessage, false);
            this.messageCenter.RegisterDefaultMessageProc(this.ProcessDefaultMessage);
            this.RegisterHandler<ResponseAccountLogin>(this.ProcessResponseAccountLogin);
            this.RegisterHandler<RequestCloseSession>(this.ProcessRequestCloseSession);
            this.RegisterHandler<RequestSendMessageToSession>(this.ProcessRequestSendMessageToSession);
            this.RegisterHandler<RequestHeartBeat>(this.ProcessRequestHeartBeat);
            this.RegisterHandler<ResponseHeartBeat>(this.ProcessResponseHeartBeat);
        }

        public string AuthService { get; set; } = "";
        public bool DisableTokenCheck { get; set; }
        public string PrivateKey { get; set; } = "";

        private void RegisterHandler<T>(Action<IChannel, T, byte[]> func) where T : RpcMeta
        {
            Action<InboundMessage> f = (inboundMessage) =>
            {
                var channel = inboundMessage.SourceConnection;
                var msg = inboundMessage.Inner as RpcMessage;
                if (msg == null) 
                {
                    this.logger.LogWarning("InboudMessage Type Error, {0}", inboundMessage.Inner);
                    return;
                }
                var meta = msg.Meta as T;
                if (meta == null) 
                {
                    this.logger.LogWarning("InboudMessage Meta Error, {0}", msg.Meta);
                    return;
                }
                func(channel, meta, msg.Body);
            };
            this.messageCenter.RegisterMessageProc(typeof(T).Name, f, false);
            this.logger.LogInformation("RegisterHandler, Type:{0}", typeof(T).Name);
        }

        private void ProcessDefaultMessage(InboundMessage inboundMessage)
        {
            var sessionInfo = inboundMessage.SourceConnection.GetSessionInfo();
            this.logger.LogWarning("ProcessDefaultMessage, SessionID:{0} MessageType:{1}",
                                    sessionInfo.SessionID, inboundMessage.MessageName);
        }

        private void ProcessResponseAccountLogin(IChannel session, ResponseAccountLogin response, byte[] body)
        {
            var destSession = this.sessionManager.GetConnection(response.SessionID);
            if (destSession == null)
            {
                this.logger.LogInformation("ProcessResponseQueryAccount Session Not Found,SessionID:{0}", response.SessionID);
                return;
            }

            var sessionInfo = destSession.GetSessionInfo();
            var playerInfo = sessionInfo.GetPlayerInfo();
            playerInfo.ActorType = response.ActorType;
            playerInfo.ActorID = response.ActorID;
            this.logger.LogInformation("ProcessResponseQueryAccount, SessionID:{0}, OpenID:{1}, Actor:{2}/{3}",
                                        sessionInfo.SessionID, playerInfo.OpenID, playerInfo.ActorType, playerInfo.ActorID);
            Task.Run(async () =>
            {
                var position = await this.FindActorPositionAsync(playerInfo.ActorType, playerInfo.ActorID).ConfigureAwait(false);
                if (position == null) 
                {
                    this.logger.LogError("ProcessResponseAccountLogin Position Fail, SessionID:{0}, Actor:{1}/{2}", 
                                                sessionInfo.SessionID, playerInfo.ActorType,
                                                playerInfo.ActorID);
                    return;
                }
                if (playerInfo.DestServerID != position.ServerID)
                {
                    playerInfo.DestServerID = position.ServerID;
                    this.logger.LogInformation("ProcessResponseQueryAccount, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                                                sessionInfo.SessionID, playerInfo.ActorType,
                                                playerInfo.ActorID, playerInfo.DestServerID);
                }

                this.messageCenter.SendMessageToServer(playerInfo.DestServerID, new RpcMessage(new NotifyNewActorSession()
                {
                    SessionID = sessionInfo.SessionID,
                    OpenID = playerInfo.OpenID,
                    ServerID = playerInfo.DestServerID,
                    ActorType = playerInfo.ActorType,
                    ActorID = playerInfo.ActorID,
                }, playerInfo.Token));
            });
        }

        private void ProcessRequestCloseSession(IChannel session, RequestCloseSession request, byte[] body)
        {
            var closeSession = this.sessionManager.GetConnection(request.SessionID);
            if (closeSession != null)
            {
                this.logger.LogInformation("ProcessRequestCloseConnection, SessionID:{0}", request.SessionID);
                var sessionInfo = closeSession.GetSessionInfo();
                sessionInfo.ShutDown();
            }
        }

        private void ProcessRequestSendMessageToSession(IChannel session, RequestSendMessageToSession request, byte[] body)
        {
            if (request.SessionId != 0)
            {
                var destSession = this.sessionManager.GetConnection(request.SessionId);
                if (destSession != null)
                {
                    this.messageCenter.SendMessage(new OutboundMessage(destSession, body));
                }
            }
            else
            {
                if (request.SessionIds != null)
                {
                    foreach (var sessionID in request.SessionIds)
                    {
                        var destSession = this.sessionManager.GetConnection(request.SessionId);
                        if (destSession != null)
                        {
                            this.messageCenter.SendMessage(new OutboundMessage(destSession, body));
                        }
                    }
                }
            }
        }

        private void ProcessRequestHeartBeat(IChannel session, RequestHeartBeat request, byte[] body)
        {
            var response = new ResponseHeartBeat() { MilliSeconds = request.MilliSeconds, };
            var sessionInfo = session.GetSessionInfo();
            sessionInfo.PutOutboundMessage(new OutboundMessage(session, new RpcMessage(response, null)));
        }

        private void ProcessResponseHeartBeat(IChannel session, ResponseHeartBeat response, byte[] body)
        {
            var sessionInfo = session.GetSessionInfo();
            var costTime = Platform.GetMilliSeconds() - response.MilliSeconds;
            if (costTime > 50)
            {
                this.logger.LogWarning("ProcessResponseHeartBeat, SessionID:{0} CostTime:{1}", sessionInfo.SessionID, costTime);
            }
            sessionInfo.ActiveTime = Platform.GetMilliSeconds();
        }

        private void ProcessWebSocketMessage(InboundMessage inboundMessage)
        {
            var session = inboundMessage.SourceConnection;
            var msg = inboundMessage.Inner as byte[];
            ArgumentNullException.ThrowIfNull(msg);
            var sessionInfo = inboundMessage.SourceConnection.GetSessionInfo();
            if (sessionInfo.OnClosed == null) 
            {
                sessionInfo.OnClosed = this.ProcessWebSocketClosed;
            } 
            var playerInfo = sessionInfo.GetPlayerInfo();
            if (playerInfo.DestServerID != 0)
            {
               _ = this.ProcessWebSocketCommonMessage(session, msg).ConfigureAwait(false);
            }
            else
            {
                _ = this.ProcessWebSocketFirstMessage(session, msg).ConfigureAwait(false);
            }
        }

        // 1000这个量级的并发度应该就够用了
        static readonly Random random = new Random();
        private static int RandomLoginServer => random.Next(0, 1024 * 2);
        private static ThreadLocal<PlacementFindActorPositionRequest> findActorRequestCache = new ThreadLocal<PlacementFindActorPositionRequest>(() => new PlacementFindActorPositionRequest());

        private async ValueTask<PlacementFindActorPositionResponse?> FindActorPositionAsync(string actorType, string actorID) 
        {
            var findPositionReq = findActorRequestCache.Value;
            ArgumentNullException.ThrowIfNull(findPositionReq);
            findPositionReq.ActorType = actorType;
            findPositionReq.ActorID = actorID;
            var position = await this.placement.FindActorPositonAsync(findPositionReq).ConfigureAwait(false);
            return position;
        }

        private async ValueTask ProcessQuickConnect(IChannel session, 
                                                IConnectionSessionInfo sessionInfo, 
                                                GatewayPlayerSessionInfo playerInfo, 
                                                string actorType, 
                                                string actorID)
        {
            playerInfo.ActorType = actorType;
            playerInfo.ActorID = actorID;

            var position = await this.FindActorPositionAsync(playerInfo.ActorType, playerInfo.ActorID).ConfigureAwait(false);
            if (position == null)
            {
                this.logger.LogError("ProcessQuickConnect Position Fail, SessionID:{0}, Actor:{1}/{2}",
                                            sessionInfo.SessionID, playerInfo.ActorType,
                                            playerInfo.ActorID);
                return;
            }
            if (playerInfo.DestServerID != position.ServerID) 
            {
                playerInfo.DestServerID = position.ServerID;
                this.logger.LogInformation("ProcessResponseQueryAccount, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                                            sessionInfo.SessionID, playerInfo.ActorType,
                                            playerInfo.ActorID, playerInfo.DestServerID);
            }

            this.messageCenter.SendMessageToServer(playerInfo.DestServerID, new RpcMessage(new NotifyNewActorSession()
            {
                SessionID = sessionInfo.SessionID,
                OpenID = playerInfo.OpenID,
                ServerID = playerInfo.DestServerID,
                ActorType = playerInfo.ActorType,
                ActorID = playerInfo.ActorID,
            }, playerInfo.Token));
        }

        const int ErrCheckSum = 10001;
        const int ErrTokenFields = 10002;

        private byte[] GenerateErrorMessage(int code, string msg) 
        {
            return Encoding.UTF8.GetBytes(string.Format("{\"error_code\":{0}, \"msg\":\"{1}\"}", code, msg));
        }

        private async ValueTask ProcessWebSocketFirstMessage(IChannel session, byte[] body)
        {
            // 一个包是一个JSON字符串
            //1. 包含`open_id`, `server_id`, `timestamp`, `check_sum`
            //2. 可选包含`actor_type`, `actor_id`
            var sessionInfo = session.GetSessionInfo();
            var playerInfo = sessionInfo.GetPlayerInfo();
            var memory = new Memory<byte>(body);
            var firstPacket = memory.DecodeFirstMessage(body.Length);
            if (this.DisableTokenCheck || firstPacket.ComputeHash(this.PrivateKey)) 
            {
                if (!(firstPacket.ContainsKey("open_id") && firstPacket.ContainsKey("server_id")))
                {
                    this.messageCenter.SendMessage(new OutboundMessage(session, GenerateErrorMessage(ErrTokenFields, "token fields error")));
                    sessionInfo.ShutDown();
                    return;
                }

                var OpenID = firstPacket["open_id"].ToString();
                var ServerID = Convert.ToInt32(firstPacket["server_id"].ToString());

                playerInfo.OpenID = OpenID;
                playerInfo.DestServerID = ServerID;
                this.logger.LogInformation("WebSocketSession Login, SessionID:{0}, OpenID:{1}, ServerID:{2}",
                                            sessionInfo.SessionID, OpenID, ServerID);

                //这边还要处理断线重来
                if (firstPacket.ContainsKey("actor_type") && firstPacket.ContainsKey("actor_id"))
                {
                    await this.ProcessQuickConnect(session,
                                                   sessionInfo,
                                                   playerInfo,
                                                   firstPacket["actor_type"].ToString(),
                                                   firstPacket["actor_id"].ToString()).ConfigureAwait(false);
                }
                else 
                {
                    playerInfo.Token = body;

                    //这边需要通过账号信息, 查找目标Actor的位置
                    var position =  await this.FindActorPositionAsync(this.AuthService, RandomLoginServer.ToString()).ConfigureAwait(false);
                    if (position == null)
                    {
                        this.logger.LogError("ProcessWebSocketFirstMessage Position Fail, SessionID:{0}, Actor:{1}/{2}",
                                                    sessionInfo.SessionID, playerInfo.ActorType,
                                                    playerInfo.ActorID);
                        return;
                    }
                    var req = new RpcMessage(new RequestAccountLogin()
                    {
                        OpenID = playerInfo.OpenID,
                        ServerID = playerInfo.DestServerID,
                        SessionID = sessionInfo.SessionID,
                    }, body);
                    this.messageCenter.SendMessageToServer(position.ServerID, req);
                }
            }
            else 
            {
                logger.LogInformation("ProcessWebSocketFirstMessage CheckSum Fail, SessionID:{0}", sessionInfo.SessionID);
                this.messageCenter.SendMessage(new OutboundMessage(session, GenerateErrorMessage(ErrCheckSum, "check sum fail")));
                sessionInfo.ShutDown();
            }
        }
        private async ValueTask ProcessWebSocketCommonMessage(IChannel session, byte[] buffer) 
        {
            var sessionInfo = session.GetSessionInfo();
            var playerInfo = sessionInfo.GetPlayerInfo();
            if (string.IsNullOrEmpty(playerInfo.ActorType)) 
            {
                this.logger.LogError("WebSocketSession Invalid Dest Server, SessionID:{0}", sessionInfo.SessionID);
                return;
            }

            var position = await this.FindActorPositionAsync(playerInfo.ActorType, playerInfo.ActorID).ConfigureAwait(false);
            if (position == null)
            {
                this.logger.LogError("ProcessWebSocketCommonMessage Position Fail, SessionID:{0}, Actor:{1}/{2}",
                                            sessionInfo.SessionID, playerInfo.ActorType,
                                            playerInfo.ActorID);
                return;
            }
            if (playerInfo.DestServerID != position.ServerID) 
            {
                playerInfo.DestServerID = position.ServerID;
                this.logger.LogInformation("WebSocketSession, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                                            sessionInfo.SessionID, playerInfo.ActorType, playerInfo.ActorID,
                                            playerInfo.DestServerID);
            }

            this.messageCenter.SendMessageToServer(playerInfo.DestServerID, new RpcMessage(new NotifyNewActorMessage()
            {
                ActorType = playerInfo.ActorType,
                ActorID = playerInfo.ActorID,
                SessionId = sessionInfo.SessionID,
            }, buffer));
        }

        private void ProcessWebSocketClosed(IChannel channel) 
        {
            _ = this.ProcessWebSocketClose(channel);
        }

        private async ValueTask ProcessWebSocketClose(IChannel session)
        {
            var sessionInfo = session.GetSessionInfo();
            try
            {
                if (!sessionInfo.IsActive)
                    return;
                var playerInfo = sessionInfo.GetPlayerInfo();
                var position = await this.FindActorPositionAsync(playerInfo.ActorType, playerInfo.ActorID).ConfigureAwait(false);
                if (position == null)
                {
                    this.logger.LogError("ProcessWebSocketClose Position Fail, SessionID:{0}, Actor:{1}/{2}",
                                                sessionInfo.SessionID, playerInfo.ActorType,
                                                playerInfo.ActorID);
                    return;
                }

                var closeMessage = new RpcMessage(new NotifyActorSessionAborted()
                {
                    SessionID = sessionInfo.SessionID,
                    ActorType = playerInfo.ActorType,
                    ActorID = playerInfo.ActorID,
                }, null);

                this.messageCenter.SendMessageToServer(position.ServerID, closeMessage);
                this.logger.LogInformation("WebSocketSession OnClose, SessionID:{0}, Actor:{1}/{2}, Dest ServerID:{3}",
                                            sessionInfo.SessionID, playerInfo.ActorType, playerInfo.ActorID, position.ServerID);
            }
            catch (Exception e)
            {
                this.logger.LogError("WebSocketSession OnClose, SessionID:{0}, Exception:{1}", sessionInfo.SessionID, e);
            }
            finally
            {
                this.sessionManager.RemoveConnection(sessionInfo.SessionID);
            }
        }
    }
}
