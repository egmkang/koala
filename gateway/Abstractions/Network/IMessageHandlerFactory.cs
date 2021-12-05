using System;
using DotNetty.Buffers;
using DotNetty.Transport.Channels;

namespace Abstractions.Network
{
    public interface IMessageCodec 
    {
        string CodecName { get; }
        object Encode(IByteBufferAllocator allocator, object msg);
        (long length, string typeName, object msg) Decode(IByteBuffer input);
    }

    public interface IMessageHandlerFactory
    {
        IChannelHandler NewHandler();

        IMessageCodec Codec { get; set; }
    }
}
