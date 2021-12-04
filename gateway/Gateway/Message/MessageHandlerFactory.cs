using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.Extensions.Logging;
using DotNetty.Codecs;
using Abstractions.Network;

namespace Gateway.Message
{
    public sealed class MessageHandlerFactory : IMessageHandlerFactory
    {
        private ILoggerFactory loggerFactory;
        private IServiceProvider serviceProvider;
        private IMessageCenter messageCenter;

        public MessageHandlerFactory(IServiceProvider serviceProvider, ILoggerFactory loggerFactory, IMessageCenter messageCenter)
        {
            this.messageCenter = messageCenter;
            this.serviceProvider = serviceProvider;
            this.loggerFactory = loggerFactory;
        }

        public IMessageCodec Codec { get; set; }

        public ByteToMessageDecoder NewHandler()
        {
            return new MessageHandler(this.serviceProvider, this.loggerFactory, this.messageCenter, this.Codec);
        }
    }
}
