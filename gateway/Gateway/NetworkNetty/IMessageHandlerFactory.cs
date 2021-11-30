using System;
using System.Collections.Generic;
using System.Text;
using DotNetty.Buffers;
using DotNetty.Codecs;

namespace Gateway.NetworkNetty
{
    public interface IMessageCodec 
    {
        string CodecName { get; }
        IByteBuffer Encode(IByteBufferAllocator allocator, object msg);
        (long length, string typeName, object msg) Decode(IByteBuffer input);
    }

    public interface IMessageHandlerFactory
    {
        ByteToMessageDecoder NewHandler();

        IMessageCodec Codec { get; set; }
    }
}
