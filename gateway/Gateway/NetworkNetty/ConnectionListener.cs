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


namespace Gateway.NetworkNetty
{
    public sealed class ConnectionListener : IConnectionListener
    {
        private IEventLoopGroup bossGroup;
        private IEventLoopGroup workGroup;
        private NetworkConfiguration config;
        private readonly ILogger logger;
        private readonly IConnectionManager connectionManager;
        private readonly IConnectionSessionInfoFactory channelSessionInfoFactory;
        private readonly List<ServerBootstrap> ports = new List<ServerBootstrap>();
        private readonly Dictionary<int, IMessageHandlerFactory> factoryContext = new Dictionary<int, IMessageHandlerFactory>();

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
            this.config = this.ServiceProvider.GetService<IOptionsMonitor<NetworkConfiguration>>().CurrentValue;
            var dispatcher = new DispatcherEventLoopGroup();
            bossGroup = dispatcher;
            workGroup = new WorkerEventLoopGroup(dispatcher, config.EventLoopCount);
        }

        public async Task BindAsync(int port, IMessageHandlerFactory handlerFactory)
        {
            factoryContext[port] = handlerFactory;

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
                .ChildOption(ChannelOption.WriteBufferLowWaterMark, this.config.WriteBufferLowWaterMark)
                .ChildHandler(new ActionChannelInitializer<IChannel>((channel) =>
                {
                    var factory = this.factoryContext[(channel.LocalAddress as IPEndPoint).Port];

                    var info = this.channelSessionInfoFactory.NewSessionInfo(factory);
                    channel.GetAttribute(ChannelExt.SESSION_INFO).Set(info);

                    var localPort = (channel.LocalAddress as IPEndPoint).Port;

                    info.RemoteAddress = channel.RemoteAddress as IPEndPoint;

                    this.connectionManager.AddConnection(channel);

                    IChannelPipeline pipeline = channel.Pipeline;
                    pipeline.AddLast("TimeOut", new IdleStateHandler(this.config.ReadTimeout, this.config.WriteTimeout, this.config.ReadTimeout));
                    pipeline.AddLast(factory.NewHandler());

                    logger.LogInformation("NewSession SessionID:{0} IpAddr:{1}, CodecName:{2}",
                            info.SessionID, info.RemoteAddress?.ToString(), factory.Codec.CodecName);
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
