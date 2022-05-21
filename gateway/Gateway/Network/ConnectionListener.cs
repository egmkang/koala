using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using System.Net;
using System.Runtime.InteropServices;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Options;
using DotNetty.Transport.Bootstrapping;
using DotNetty.Transport.Channels;
using DotNetty.Codecs;
using DotNetty.Transport.Libuv;
using DotNetty.Buffers;
using DotNetty.Handlers.Timeout;
using Abstractions.Network;
using DotNetty.Codecs.Http;
using DotNetty.Codecs.Http.WebSockets.Extensions.Compression;
using DotNetty.Codecs.Http.WebSockets;

namespace Gateway.Network
{
    public sealed class ConnectionListener : IConnectionListener
    {
        private IEventLoopGroup? bossGroup;
        private IEventLoopGroup? workGroup;
        private NetworkConfiguration? config;
        private readonly ILogger logger;
        private readonly IConnectionManager connectionManager;
        private readonly IConnectionSessionInfoFactory channelSessionInfoFactory;
        private readonly List<ServerBootstrap> ports = new List<ServerBootstrap>();
        private readonly Dictionary<int, Action<IChannel>> factoryContext = new Dictionary<int, Action<IChannel>>();

        public IServiceProvider ServiceProvider { get; private set; }

        public ConnectionListener(IServiceProvider provider,
            ILoggerFactory loggerFactory,
            IConnectionManager connectionManager,
            IConnectionSessionInfoFactory channelSessionInfoFactory)
        {
            this.connectionManager = connectionManager;
            this.channelSessionInfoFactory = channelSessionInfoFactory;
            this.ServiceProvider = provider;
            this.logger = loggerFactory.CreateLogger("Sockets");
        }

        public void Init()
        {
            if (this.bossGroup != null)
            { 
                return;
            }

            this.config = this.ServiceProvider.GetRequiredService<IOptionsMonitor<NetworkConfiguration>>().CurrentValue;
            var dispatcher = new DispatcherEventLoopGroup();
            bossGroup = dispatcher;
            workGroup = new WorkerEventLoopGroup(dispatcher, config.EventLoopCount);
        }

        private ServerBootstrap MakeBootStrap() 
        {
            ArgumentNullException.ThrowIfNull(this.config);

            var bootstrap = new ServerBootstrap();
            bootstrap.Group(this.bossGroup, this.workGroup)
                .Channel<TcpServerChannel>();

            if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux)
                || RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
            {
                bootstrap
                    .Option(ChannelOption.SoReuseport, true)
                    .ChildOption(ChannelOption.SoReuseaddr, true);
            }

            bootstrap
                .Option(ChannelOption.SoBacklog, this.config.SoBackLog)
                .Option(ChannelOption.SoRcvbuf, this.config.RecvWindowSize)
                .Option(ChannelOption.SoSndbuf, this.config.SendWindowSize)
                .Option(ChannelOption.SoReuseaddr, true)
                .Option(ChannelOption.Allocator, PooledByteBufferAllocator.Default)
                .ChildOption(ChannelOption.TcpNodelay, true)
                .ChildOption(ChannelOption.SoKeepalive, true)
                .ChildOption(ChannelOption.WriteBufferHighWaterMark, this.config.WriteBufferHighWaterMark)
                .ChildOption(ChannelOption.WriteBufferLowWaterMark, this.config.WriteBufferLowWaterMark);

            return bootstrap;
        }

        public async Task BindWebSocketAsync(int port, string websocketPath, IMessageHandlerFactory handlerFactory) 
        {
            ArgumentNullException.ThrowIfNull(this.config);

            factoryContext[port] = (channel) => 
            {
                var info = this.channelSessionInfoFactory.NewSessionInfo(handlerFactory);
                info.ConnectionType = ConnectionType.WebSocket;
                channel.GetAttribute(ChannelExt.SESSION_INFO).Set(info);

                var addr = channel.RemoteAddress as IPEndPoint;
                ArgumentNullException.ThrowIfNull(addr);
                info.RemoteAddress = addr;

                this.connectionManager.AddConnection(channel);

                IChannelPipeline pipeline = channel.Pipeline;
                pipeline.AddLast("TimeOut", new IdleStateHandler(this.config.ReadTimeout, this.config.WriteTimeout, this.config.ReadTimeout));
                pipeline.AddLast(new HttpServerCodec());
                pipeline.AddLast(new HttpObjectAggregator(65536));
                pipeline.AddLast(new WebSocketServerCompressionHandler());
                pipeline.AddLast(new WebSocketServerProtocolHandler(
                    websocketPath: websocketPath,
                    subprotocols: null,
                    allowExtensions: true,
                    maxFrameSize: 65536,
                    allowMaskMismatch: true,
                    checkStartsWith: false,
                    dropPongFrames: true,
                    enableUtf8Validator: false));
                pipeline.AddLast(new WebSocketServerHttpHandler());
                pipeline.AddLast(new WebSocketFrameAggregator(65536));
                pipeline.AddLast(handlerFactory.NewHandler());

                logger.LogInformation("NewWebSocketSession SessionID:{0} IpAddr:{1}, CodecName:{2}",
                        info.SessionID, info.RemoteAddress?.ToString(), handlerFactory.Codec.CodecName);
            };

            var bootstrap = this.MakeBootStrap();
            bootstrap.ChildHandler(new ActionChannelInitializer<IChannel>((channel) =>
            {
                var endPoint = channel.LocalAddress as IPEndPoint;
                if (endPoint == null) 
                {
                    logger.LogError("newChannel Error, Don't have EndPoint");
                    return;
                }
                var port = endPoint.Port;
                var factory = this.factoryContext[port];
                factory(channel);
            }));

            await bootstrap.BindAsync(port);
            ports.Add(bootstrap);
            logger.LogInformation("Listen Port:{0}, {1}, Codec:{2}", port, handlerFactory.NewHandler().GetType(), handlerFactory.Codec.GetType());
        }

        public async Task BindAsync(int port, IMessageHandlerFactory handlerFactory)
        {
            ArgumentNullException.ThrowIfNull(this.config);

            factoryContext[port] = (channel) =>
            {
                var info = this.channelSessionInfoFactory.NewSessionInfo(handlerFactory);
                info.ConnectionType = ConnectionType.Socket;
                channel.GetAttribute(ChannelExt.SESSION_INFO).Set(info);

                var addr = channel.RemoteAddress as IPEndPoint;
                ArgumentNullException.ThrowIfNull(addr);
                info.RemoteAddress = addr;

                this.connectionManager.AddConnection(channel);

                IChannelPipeline pipeline = channel.Pipeline;
                pipeline.AddLast("TimeOut", new IdleStateHandler(this.config.ReadTimeout, this.config.WriteTimeout, this.config.ReadTimeout));
                pipeline.AddLast(handlerFactory.NewHandler());

                logger.LogInformation("NewSession SessionID:{0} IpAddr:{1}, CodecName:{2}",
                        info.SessionID, info.RemoteAddress?.ToString(), handlerFactory.Codec.CodecName);
            };

            var bootstrap = this.MakeBootStrap();
            bootstrap.ChildHandler(new ActionChannelInitializer<IChannel>((channel) =>
            {
                var endPoint = channel.RemoteAddress as IPEndPoint;
                if (endPoint == null) 
                {
                    logger.LogError("NewChannel Error, Don't have a EndPoint");
                    return;
                }
                var port = endPoint.Port;
                var factory = this.factoryContext[port];
                factory(channel);
            }));

            await bootstrap.BindAsync(port);
            ports.Add(bootstrap);
            logger.LogInformation("Listen Port:{0}, {1}, Codec:{2}", port, handlerFactory.NewHandler().GetType(), handlerFactory.Codec.GetType());
        }


        public async Task ShutdDownAsync()
        {
            if (this.bossGroup != null) await this.bossGroup.ShutdownGracefullyAsync(TimeSpan.FromSeconds(0.5), TimeSpan.FromSeconds(0.5)).ConfigureAwait(false);
            if(this.workGroup != null) await this.workGroup.ShutdownGracefullyAsync(TimeSpan.FromSeconds(0.5), TimeSpan.FromSeconds(0.5)).ConfigureAwait(false);
        }
    }
}
