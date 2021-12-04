using System;
using System.Buffers;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Gateway.Message;
using DotNetty.Buffers;
using DotNetty.Common.Utilities;

namespace test
{
    [TestClass]
    public class CodecTest
    {
        readonly RpcMessageCodec rpcCodec = new RpcMessageCodec();

        private static void RpcMessageEqual(RpcMessage m1, int s1, RpcMessage m2, int s2)
        {
            Assert.AreEqual(s1, s2);
            CollectionAssert.AreEqual(m1.Body, m2.Body);
            Assert.AreEqual(m1.Meta.GetType(), m2.Meta.GetType());
            Assert.AreEqual((m1.Meta as RequestHeartBeat).MilliSeconds, (m2.Meta as RequestHeartBeat).MilliSeconds);
        }

        readonly IByteBufferAllocator allocator = PooledByteBufferAllocator.Default;

        [TestMethod]
        public void TestRpcCodec() 
        {
            var req = new RequestHeartBeat() { MilliSeconds = 123 };
            var rpcMessage = new RpcMessage(req, null);

            var buffer = rpcCodec.Encode(allocator, rpcMessage) as IByteBuffer;
            var bufferLength = buffer.ReadableBytes;

            var (length, typeName, msg) = rpcCodec.Decode(buffer);

            RpcMessageEqual(rpcMessage, bufferLength, msg as RpcMessage, (int)length);

            ReferenceCountUtil.Release(buffer);
        }

        [TestMethod]
        public void TestRpcCodecWithBody() 
        {
            var inputBody = new byte[3] { 1, 2, 3 };
            var req = new RequestHeartBeat() { MilliSeconds = 456 };
            var rpcMessage = new RpcMessage(req, inputBody);

            var buffer = rpcCodec.Encode(allocator, rpcMessage) as IByteBuffer;
            var bufferLength = buffer.ReadableBytes;

            var (length, typeName, msg) = rpcCodec.Decode(buffer);

            RpcMessageEqual(rpcMessage, bufferLength, msg as RpcMessage, (int)length);

            ReferenceCountUtil.Release(buffer);
        }

        [TestMethod]
        public void TestMiltiMessagesRpcCodec() 
        {
            var body1 = new byte[3] { 4, 5, 6 };
            var reqHeartBeat1 = new RequestHeartBeat() { MilliSeconds = 123 };
            var rpcMessage1 = new RpcMessage(reqHeartBeat1, body1);
            var buffer1 = rpcCodec.Encode(allocator, rpcMessage1) as IByteBuffer;
            var bufferLength1 = buffer1.ReadableBytes;

            var body2 = new byte[4] { 7, 8, 9, 10 };
            var reqHeartBeat2 = new RequestHeartBeat() { MilliSeconds = 34234234 };
            var rpcMessage2 = new RpcMessage(reqHeartBeat2, body2);
            var buffer2 = rpcCodec.Encode(allocator, rpcMessage2) as IByteBuffer;
            var bufferLength2 = buffer2.ReadableBytes;


            var buffer = allocator.Buffer();
            buffer.WriteBytes(buffer1);
            buffer.WriteBytes(buffer2);

            var (length1, typeName1, msg1) = rpcCodec.Decode(buffer);
            RpcMessageEqual(rpcMessage1, bufferLength1, msg1 as RpcMessage, (int)length1);

            var (length2, typeName2, msg2) = rpcCodec.Decode(buffer);
            RpcMessageEqual(rpcMessage2, bufferLength2, msg2 as RpcMessage, (int)length2);
        }
    }
}
