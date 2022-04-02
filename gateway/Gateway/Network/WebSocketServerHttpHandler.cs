using DotNetty.Buffers;
using DotNetty.Codecs.Http;
using DotNetty.Transport.Channels;
using static DotNetty.Codecs.Http.HttpResponseStatus;

namespace Gateway.Network
{
    public sealed class WebSocketServerHttpHandler : SimpleChannelInboundHandler2<IFullHttpRequest>
    {
        protected override void ChannelRead0(IChannelHandlerContext context, IFullHttpRequest request)
        {
            var res = new DefaultFullHttpResponse(request.ProtocolVersion, NotFound, context.Allocator.Buffer(0));
            SendHttpResponse(context, request, res);
        }

        static void SendHttpResponse(IChannelHandlerContext context, IFullHttpRequest request, IFullHttpResponse response)
        {
            // Generate an error page if response getStatus code is not OK (200).
            HttpResponseStatus responseStatus = response.Status;
            if (responseStatus.Code != 200)
            {
                ByteBufferUtil.WriteUtf8(response.Content, responseStatus.ToString());
                HttpUtil.SetContentLength(response, response.Content.ReadableBytes);
            }

            // Send the response and close the connection if necessary.
            var keepAlive = HttpUtil.IsKeepAlive(request) && responseStatus.Code == 200;
            HttpUtil.SetKeepAlive(response, keepAlive);
            var future = context.WriteAndFlushAsync(response);
            if (!keepAlive)
            {
                future.CloseOnComplete(context.Channel);
            }
        }
    }
}
