using System;
using Microsoft.Extensions.Logging;
using DotNetty.Handlers.Timeout;
using DotNetty.Transport.Channels;
using DotNetty.Codecs.Http.WebSockets;
using Abstractions.Network;
using Gateway.Utils;
using Gateway.Network;

namespace Gateway.Message
{
    public sealed class WebSocketServerFrameHandler : SimpleChannelInboundHandler<WebSocketFrame>
    {
        private readonly ILogger logger;
        private readonly IServiceProvider serviceProvider;
        private readonly IMessageCenter messageCenter;
        private readonly IMessageCodec codec;

        public WebSocketServerFrameHandler(IServiceProvider serviceProvider,
                                        ILoggerFactory loggerFactory,
                                        IMessageCenter messageCenter,
                                        IMessageCodec codec) 
        {
            this.logger = loggerFactory.CreateLogger("Network");
            this.serviceProvider = serviceProvider;
            this.messageCenter = messageCenter;
            this.codec = codec;
        }

        public override bool IsSharable => false;

        protected override void ChannelRead0(IChannelHandlerContext context, WebSocketFrame frame)
        {
            if (frame is TextWebSocketFrame || frame is BinaryWebSocketFrame) 
            {
                var currentMilliSeconds = Platform.GetMilliSeconds();
                var sessionInfo = context.Channel.GetSessionInfo();

                var buffer = frame.Content;

                var (length, typeName, message) = this.codec.Decode(buffer);
                if (length == 0)
                {
                    return;
                }
                if (message == null) 
                {
                    logger.LogError("Decode Fail, SessionID:{0}", context.Channel.GetSessionInfo().SessionID);
                    return;
                }

                //this.logger.LogTrace("DecodeMessage:{0}", typeName);

                sessionInfo.ActiveTime = currentMilliSeconds;

                var inboundMessage = new InboundMessage(context.Channel, typeName, message, Platform.GetMilliSeconds());
                this.messageCenter.OnReceiveMessage(inboundMessage);
                return;
            }
        }
        public override void ChannelInactive(IChannelHandlerContext ctx)
        {
            var sessionInfo = ctx.Channel.GetSessionInfo();

            this.logger.LogInformation("SessionID:{0} Inactive", sessionInfo.SessionID);

            this.messageCenter.OnConnectionClosed(ctx.Channel);
            sessionInfo.ShutDown();

            base.ChannelInactive(ctx);
        }

        public override void ExceptionCaught(IChannelHandlerContext context, Exception exception)
        {
            var sessionInfo = context.Channel.GetSessionInfo();
            logger.LogError("SessionID:{0}, Exception:{1}", sessionInfo.SessionID, exception.Message);
            context.CloseAsync();
        }

        public override void UserEventTriggered(IChannelHandlerContext context, object evt)
        {
            var sessionInfo = context.Channel.GetSessionInfo();

            if (evt is IdleStateEvent && (evt as IdleStateEvent).State == IdleState.ReaderIdle)
            {
                logger.LogError("SessionID:{0} TimeOut, Close", sessionInfo.SessionID);
                context.CloseAsync();
            }
            else
            {
                base.UserEventTriggered(context, evt);
            }
        }
    }
}
