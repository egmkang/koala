using System;
using System.Collections.Generic;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.DependencyInjection;
using DotNetty.Buffers;
using DotNetty.Handlers.Timeout;
using DotNetty.Transport.Bootstrapping;
using DotNetty.Transport.Channels;
using DotNetty.Transport.Channels.Sockets;
using Abstractions.Network;

namespace Gateway.Network
{
    public sealed class ClientConnectionFactory : IClientConnectionFactory
    {
        private MultithreadEventLoopGroup group;
        private NetworkConfiguration config;
        private readonly object mutex = new object();
        private Dictionary<IMessageHandlerFactory, Bootstrap> bootstraps = new Dictionary<IMessageHandlerFactory, Bootstrap>();

        private readonly ILogger logger;
        private readonly IConnectionManager connectionManager;
        private readonly IConnectionSessionInfoFactory channelSessionInfoFactory;

        public IServiceProvider ServiceProvider { get; private set; }

        public ClientConnectionFactory(IServiceProvider provider,
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
            if (this.group != null) 
            {
                return;
            }
            this.config = this.ServiceProvider.GetRequiredService<IOptionsMonitor<NetworkConfiguration>>().CurrentValue;
            this.group = new MultithreadEventLoopGroup(this.config.EventLoopCount);
        }

        public async Task<IChannel> ConnectAsync(EndPoint address, IMessageHandlerFactory factory)
        {
            Bootstrap bootstrap;
            lock (mutex) 
            {
                if (!this.bootstraps.TryGetValue(factory, out bootstrap))
                {
                    bootstrap = new Bootstrap();
                    bootstrap
                        .Group(this.group)
                        .Channel<TcpSocketChannel>()
                        .Option(ChannelOption.SoRcvbuf, this.config.RecvWindowSize)
                        .Option(ChannelOption.SoSndbuf, this.config.SendWindowSize)
                        .Option(ChannelOption.Allocator, PooledByteBufferAllocator.Default)
                        .Option(ChannelOption.TcpNodelay, true)
                        .Option(ChannelOption.SoKeepalive, true)
                        .Option(ChannelOption.WriteBufferHighWaterMark, this.config.WriteBufferHighWaterMark)
                        .Option(ChannelOption.WriteBufferLowWaterMark, this.config.WriteBufferLowWaterMark)
                        .Handler(new ActionChannelInitializer<IChannel>(channel =>
                        {
                            var info = this.channelSessionInfoFactory.NewSessionInfo(factory);
                            info.ConnectionType = ConnectionType.Socket;
                            channel.GetAttribute(ChannelExt.SESSION_INFO).Set(info);

                            IChannelPipeline pipeline = channel.Pipeline;
                            pipeline.AddLast("TimeOut", new IdleStateHandler(this.config.ReadTimeout, this.config.WriteTimeout, this.config.ReadTimeout));
                            pipeline.AddLast(factory.NewHandler());

                            logger.LogInformation("New Client Session, SessionID:{0}", channel.GetSessionInfo().SessionID);
                        }));

                    this.bootstraps.TryAdd(factory, bootstrap);
                }
            }
            var channel = await bootstrap.ConnectAsync(address).ConfigureAwait(false);
            channel.GetSessionInfo().RemoteAddress = channel.RemoteAddress as IPEndPoint;
            this.connectionManager.AddConnection(channel);
            return channel;
        }

        public async Task ShutdDownAsync()
        {
            if (this.group != null) await this.group.ShutdownGracefullyAsync(TimeSpan.FromSeconds(0.5), TimeSpan.FromSeconds(0.5)).ConfigureAwait(false);
        }
    }
}
