using System;
using Microsoft.Extensions.Logging;
using DotNetty.Codecs;
using Abstractions.Network;
using Microsoft.Extensions.DependencyInjection;
using DotNetty.Transport.Channels;

namespace Gateway.Message
{
    public class MessageHandlerFactoryBase
    {
        protected readonly ILoggerFactory loggerFactory;
        protected readonly IServiceProvider serviceProvider;
        protected readonly IMessageCenter messageCenter;

        public MessageHandlerFactoryBase(IServiceProvider serviceProvider)
        {
            this.serviceProvider = serviceProvider;
            this.messageCenter = this.serviceProvider.GetRequiredService<IMessageCenter>();
            this.loggerFactory = this.serviceProvider.GetRequiredService<ILoggerFactory>();
        }

        public IMessageCodec Codec { get; set; }
    }

    public sealed class MessageHandlerFactory : MessageHandlerFactoryBase, IMessageHandlerFactory
    {
        public MessageHandlerFactory(IServiceProvider serviceProvider) : base(serviceProvider)
        {
        }

        public IChannelHandler NewHandler()
        {
            return new MessageHandler(this.serviceProvider, this.loggerFactory, this.messageCenter, this.Codec);
        }
    }

    public sealed class WebSocketMessageHandlerFactory : MessageHandlerFactoryBase, IMessageHandlerFactory
    {
        public WebSocketMessageHandlerFactory(IServiceProvider serviceProvider) : base(serviceProvider)
        {
        }

        public IChannelHandler NewHandler()
        {
            return new WebSocketServerFrameHandler(this.serviceProvider, this.loggerFactory, this.messageCenter, this.Codec);
        }
    }
}
