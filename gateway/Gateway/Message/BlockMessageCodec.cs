using Abstractions.Network;
using DotNetty.Buffers;
using DotNetty.Codecs.Http.WebSockets;

namespace Gateway.Message
{
    public class BlockMessageCodec : IMessageCodec
    {
        public string CodecName => "WebSocketBlockMessage";

        public (long length, string typeName, object msg) Decode(IByteBuffer input)
        {
            var bytes = new byte[input.ReadableBytes];
            input.ReadBytes(bytes);
            return (bytes.Length, CodecName, bytes);
        }

        public object Encode(IByteBufferAllocator allocator, object msg)
        {
            var bytes = msg as byte[];
            return new BinaryWebSocketFrame(Unpooled.WrappedBuffer(bytes));
        }
    }
}
