using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Gateway.Handler;
using Gateway.Message;
using Gateway.Network;
using Gateway.Placement;
using Gateway.Utils;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Connections;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Gateway
{
    public class Startup
    {
        private IConnectionListener connectionListener;
        private SessionManager sessionManager;
        private IMessageCenter messageCenter;
        private ILoggerFactory loggerFactory;
        private ILogger logger;
        private IPlacement placement;
        private ClientConnectionPool clientConnectionPool;
        private SessionUniqueSequence sessionUniqueSequence;

        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }
        public long ServerID { get; private set; }
        public long LeaseID { get; private set; }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env, IServiceProvider serviceProvider)
        {
            this.PrepareGateway(serviceProvider);
            _ = this.RunGateway(serviceProvider, app);
        }

        public void PrepareGateway(IServiceProvider serviceProvider) 
        {
            this.loggerFactory = serviceProvider.GetRequiredService<ILoggerFactory>();
            this.logger = this.loggerFactory.CreateLogger("Gateway");
            this.sessionManager = serviceProvider.GetRequiredService<SessionManager>();
            this.messageCenter = serviceProvider.GetRequiredService<IMessageCenter>();
            this.clientConnectionPool = serviceProvider.GetRequiredService<ClientConnectionPool>();
            this.placement = serviceProvider.GetRequiredService<IPlacement>();
            this.sessionUniqueSequence = serviceProvider.GetRequiredService<SessionUniqueSequence>();
            this.clientConnectionPool.MessageCenter = messageCenter;
            serviceProvider.GetRequiredService<MessageHandler>();

            this.placement.RegisterServerChangedEvent(this.OnAddServer, this.OnRemoveServer, this.OnOfflineServer);
        }

        public async Task RunGateway(IServiceProvider serviceProvider, IApplicationBuilder app) 
        {
            var interval = 5;
            var port = 15000;
            var address = "127.0.0.1:15000";
            var wsPath = "/ws";
            var placementAddress = "http://10.1.1.192:2379";

            this.PrepareGateway(serviceProvider);
            this.placement.SetPlacementServerInfo(placementAddress);

            _ = this.ListenSocketAsync(serviceProvider, port);
            this.ListenWebSocket(app, serviceProvider, wsPath);

            try
            {
                ServerID = await this.placement.GenerateServerIDAsync();
                this.sessionUniqueSequence.SetServerID(ServerID);

                this.logger.LogInformation("GetServerID, ServerID:{0}, Address:{1}", ServerID, address);

                LeaseID = await this.placement.RegisterServerAsync(new PlacementActorHostInfo()
                {
                    ServerID = ServerID,
                    Address = address,
                    StartTime = Platform.GetMilliSeconds(),
                    TTL = interval * 3,
                    Desc = $"Gateway_{ServerID}",
                    Services = new Dictionary<string, string>() { { "IGateway", "GatewayImpl" } },
                });
                this.logger.LogInformation("RegisterServer Success, LeaseID:{0}", LeaseID);
            }
            catch (Exception e) 
            {
                this.logger.LogError("StartUp Gateway, Exception:{0}", e);
            }

            this.placement.OnException(this.OnPDKeepAliveException);
            _ = this.placement.StartPullingAsync().ContinueWith((t) =>
            {
                this.logger.LogError("PDKeepAlive Process Exit");
                NLog.LogManager.Flush();
                Environment.Exit(-1);
            });
        }
        private void OnPDKeepAliveException(Exception e) 
        {
            this.logger.LogError("PDKeepAlive, Exception:{0}", e);
        }

        private void OnAddServer(PlacementActorHostInfo serverInfo) 
        {
            Func<object> fn = () =>
            {
                var rpcMessage = new RpcMessage(new RequestHeartBeat() { MilliSeconds = Platform.GetMilliSeconds()}, null);
                return rpcMessage;
            };

            this.clientConnectionPool.OnAddServer(serverInfo.ServerID, IPEndPoint.Parse(serverInfo.Address), fn);
        }
        private void OnRemoveServer(PlacementActorHostInfo serverInfo) 
        {
            this.clientConnectionPool.OnRemoveServer(serverInfo.ServerID);
        }
        private void OnOfflineServer(PlacementActorHostInfo serverInfo) 
        {
        }

        private async Task RunTcpSession(TcpSocketSession session)
        {
            try
            {
                this.sessionManager.AddSession(session);
                await session.MainLoop().ConfigureAwait(false);
            }
            catch (Exception e)
            {
                logger.LogError("TcpSocket, SessionID:{0} Exception:{1}", session.SessionID, e);
                await session.CloseAsync();
            }
        }

        public async Task ListenSocketAsync(IServiceProvider serviceProvider, int port)
        {
            try
            {
                var listenerFactory = serviceProvider.GetRequiredService<IConnectionListenerFactory>();
                this.connectionListener = await listenerFactory.BindAsync(new IPEndPoint(0, port)).ConfigureAwait(false);
                var logger = this.loggerFactory.CreateLogger("TcpSocket");
                logger.LogInformation("Listen Port:{0} success", port);

                while (true)
                {
                    var context = await this.connectionListener.AcceptAsync().ConfigureAwait(false);
                    var sessionInfo = new DefaultSessionInfo(this.sessionUniqueSequence.NewSessionID, 0);
                    var tcpSession = new TcpSocketSession(context, sessionInfo, logger, this.messageCenter);
                    this.logger.LogInformation("TcpSocketSession Accept, SessionID:{0}, RemoteAddress:{1}", 
                                                tcpSession.SessionID, tcpSession.RemoteAddress);
                    _ = this.RunTcpSession(tcpSession);
                }
            }
            catch (Exception e)
            {
                this.logger.LogError("Exception:{0}", e);
            }
        }

        public void ListenWebSocket(IApplicationBuilder app, 
                                            IServiceProvider serviceProvider, 
                                            string path) 
        {
            var loggerFactory = serviceProvider.GetRequiredService<ILoggerFactory>();
            var logger = loggerFactory.CreateLogger("WebSocket");

            app.UseForwardedHeaders(new ForwardedHeadersOptions
            {
                ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto,
            });

            app.UseWebSockets(new WebSocketOptions()
            {
                KeepAliveInterval = TimeSpan.FromSeconds(15),
            });

            app.Use(async (context, next) =>
            {
                if (context.Request.Path == path)
                {
                    var address = context.Connection.RemoteIpAddress.ToString();
                    using (var websocket = await context.WebSockets.AcceptWebSocketAsync().ConfigureAwait(false))
                    {
                        var sessionInfo = new DefaultSessionInfo(this.sessionUniqueSequence.NewSessionID, 0);
                        var session = new WebSocketSession(websocket, address, logger, this.messageCenter, sessionInfo);
                        try
                        {
                            this.sessionManager.AddSession(session);
                            await session.MainLoop().ConfigureAwait(false);
                        }
                        catch (Exception e) 
                        {
                            logger.LogError("WebSocket, SessionID:{0}, Address:{1}, Exception:{2}",
                                sessionInfo.SessionID, address, e);
                            await session.CloseAsync().ConfigureAwait(false);
                        }
                    }
                }
                await next();
            });
        }
    }
}
