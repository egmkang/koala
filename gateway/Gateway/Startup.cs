using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Abstractions.Placement;
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
using Microsoft.Extensions.Options;

namespace Gateway
{
    public class Startup
    {
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

        public void ConfigureServices(IServiceCollection services)
        {
            services.Configure<GatewayConfiguration>((config) =>
            {
                Configuration.GetSection("Gateway").Bind(config);
            });
        }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env, IServiceProvider serviceProvider)
        {
            this.loggerFactory = serviceProvider.GetRequiredService<ILoggerFactory>();
            this.logger = this.loggerFactory.CreateLogger("Gateway");
            this.clientConnectionPool = serviceProvider.GetRequiredService<ClientConnectionPool>();

            var urls = this.Configuration["Urls"];
            var config = serviceProvider.GetRequiredService<IOptionsMonitor<GatewayConfiguration>>().CurrentValue;
            config.GatewayAddress = urls + config.WebSocketPath;
            logger.LogInformation("GatewayConfig, PD: {0}, GatewayAddress: {1}, ListenAddress: {2}", 
                                    config.PlacementDriverAddress, config.GatewayAddress, config.ListenAddress);

            WebSocketRateLimit.Limit = config.WebSocketRateLimit;

            this.PrepareGateway(serviceProvider, config);
            _ = this.RunGateway(serviceProvider, app, config);
        }

        public void PrepareGateway(IServiceProvider serviceProvider, GatewayConfiguration config) 
        {
            this.placement = serviceProvider.GetRequiredService<IPlacement>();
            this.sessionUniqueSequence = serviceProvider.GetRequiredService<SessionUniqueSequence>();

            var messageHandler = serviceProvider.GetRequiredService<Handler.GatewayMessageHandler>();
            messageHandler.PrivateKey = config.PrivateKey;
            messageHandler.DisableTokenCheck = config.DisableTokenCheck;
            messageHandler.AuthService = config.AuthService;

            this.placement.RegisterServerChangedEvent(this.OnAddServer, this.OnRemoveServer, this.OnOfflineServer);
        }

        public async Task RunGateway(IServiceProvider serviceProvider, IApplicationBuilder app, GatewayConfiguration config) 
        {
            var port = Convert.ToInt32(config.ListenAddress.Split(':').Last());

            this.placement.SetPlacementServerInfo(config.PlacementDriverAddress);

            this.ListenWebSocket(app, serviceProvider, config.WebSocketPath);

            try
            {
                ServerID = await this.placement.GenerateServerIDAsync();
                this.sessionUniqueSequence.SetServerID(ServerID);

                this.logger.LogInformation("GetServerID, ServerID:{0}, Address:{1}", ServerID, config.ListenAddress);

                LeaseID = await this.placement.RegisterServerAsync(new PlacementActorHostInfo()
                {
                    ServerID = ServerID,
                    Address = config.ListenAddress,
                    StartTime = Platform.GetMilliSeconds(),
                    TTL = config.KeepAliveInterval * 3,
                    Desc = $"Gateway_{ServerID}",
                    Services = new Dictionary<string, string>() { { "IGateway", "GatewayImpl" } },
                    Labels = new Dictionary<string, string>() { { "GatewayAddress" , config.GatewayAddress} },
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
        }
    }
}
