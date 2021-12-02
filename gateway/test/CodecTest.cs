using System;
using System.Buffers;
using System.Text;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Gateway.Message;
using DotNetty.Buffers;
using DotNetty.Common.Utilities;

namespace test
{
    internal class MemorySegment<T> : ReadOnlySequenceSegment<T>
    {
        public MemorySegment(ReadOnlyMemory<T> memory)
        {
            Memory = memory;
        }

        public MemorySegment<T> Append(ReadOnlyMemory<T> memory)
        {
            var segment = new MemorySegment<T>(memory)
            {
                RunningIndex = RunningIndex + Memory.Length
            };

            Next = segment;

            return segment;
        }
    }

    [TestClass]
    public class CodecTest
    {
        readonly RpcMessageCodec rpcCodec = new RpcMessageCodec();
        readonly RpcMessageCodec2 rpcCodec2 = new RpcMessageCodec2();

        class MockBufferWriter : IBufferWriter<byte>
        {
            public void Advance(int count)
            {
                throw new NotImplementedException();
            }

            public Memory<byte> GetMemory(int sizeHint = 0)
            {
                return MemoryPool<byte>.Shared.Rent(sizeHint).Memory;
            }

            public Span<byte> GetSpan(int sizeHint = 0)
            {
                return MemoryPool<byte>.Shared.Rent(sizeHint).Memory.Span;
            }
        }

        [TestMethod]
        public void TestRpcCodec()
        {
            var req = new RequestHeartBeat() { MilliSeconds = 123 };
            var rpcMessage = new RpcMessage(req, null);

            var (memory, size) = rpcCodec.Encode(new MockBufferWriter(), rpcMessage);

            var messageSize = rpcCodec.Decode(new ReadOnlySequence<byte>(memory).Slice(0, size), out var decodedMessage);

            RpcMessageEqual(rpcMessage, size, decodedMessage, messageSize);
        }
        [TestMethod]
        public void TestRpcCodecWithBody()
        {
            var inputBody = new byte[3] { 1, 2, 3 };
            var req = new RequestHeartBeat() { MilliSeconds = 456 };
            var rpcMessage = new RpcMessage(req, inputBody);

            var (memory, size) = rpcCodec.Encode(new MockBufferWriter(), rpcMessage);

            var messageSize = rpcCodec.Decode(new ReadOnlySequence<byte>(memory).Slice(0, size), out var decodedMessage);
            RpcMessageEqual(rpcMessage, size, decodedMessage, messageSize);
        }

        private static void RpcMessageEqual(RpcMessage m1, int s1, RpcMessage m2, int s2)
        {
            Assert.AreEqual(s1, s2);
            CollectionAssert.AreEqual(m1.Body, m2.Body);
            Assert.AreEqual(m1.Meta.GetType(), m2.Meta.GetType());
            Assert.AreEqual((m1.Meta as RequestHeartBeat).MilliSeconds, (m2.Meta as RequestHeartBeat).MilliSeconds);
        }

        [TestMethod]
        public void TestMultiMessagesRpcCodec() 
        {
            var body1 = new byte[3] { 4, 5, 6 };
            var reqHeartBeat1 = new RequestHeartBeat() { MilliSeconds = 123 };
            var rpcMessage1 = new RpcMessage(reqHeartBeat1, body1);
            var (memory1, size1) = rpcCodec.Encode(new MockBufferWriter(), rpcMessage1);

            var body2 = new byte[4] { 7, 8, 9, 10 };
            var reqHeartBeat2 = new RequestHeartBeat() { MilliSeconds = 34234234 };
            var rpcMessage2 = new RpcMessage(reqHeartBeat2, body2);
            var (memory2, size2) = rpcCodec.Encode(new MockBufferWriter(), rpcMessage2);


            var first = new MemorySegment<byte>(memory1.Slice(0, size1));
            var last = first.Append(memory2.Slice(0, size2));

            var sequence = new ReadOnlySequence<byte>(first, 0, last, last.Memory.Length);

            var messageSize1 = rpcCodec.Decode(sequence, out var decodedMessage1);
            RpcMessageEqual(rpcMessage1, size1, decodedMessage1, messageSize1);

            var messageSize2 = rpcCodec.Decode(sequence.Slice(messageSize1), out var decodedMessage2);
            RpcMessageEqual(rpcMessage2, size2, decodedMessage2, messageSize2);
        }

        readonly IByteBufferAllocator allocator = PooledByteBufferAllocator.Default;

        [TestMethod]
        public void TestRpcCodec2() 
        {
            var req = new RequestHeartBeat() { MilliSeconds = 123 };
            var rpcMessage = new RpcMessage(req, null);

            var buffer = rpcCodec2.Encode(allocator, rpcMessage);
            var bufferLength = buffer.ReadableBytes;

            var (length, typeName, msg) = rpcCodec2.Decode(buffer);

            RpcMessageEqual(rpcMessage, bufferLength, msg as RpcMessage, (int)length);

            ReferenceCountUtil.Release(buffer);
        }

        [TestMethod]
        public void TestRpcCodec2WithBody() 
        {
            var inputBody = new byte[3] { 1, 2, 3 };
            var req = new RequestHeartBeat() { MilliSeconds = 456 };
            var rpcMessage = new RpcMessage(req, inputBody);

            var buffer = rpcCodec2.Encode(allocator, rpcMessage);
            var bufferLength = buffer.ReadableBytes;

            var (length, typeName, msg) = rpcCodec2.Decode(buffer);

            RpcMessageEqual(rpcMessage, bufferLength, msg as RpcMessage, (int)length);

            ReferenceCountUtil.Release(buffer);
        }

        [TestMethod]
        public void TestMiltiMessagesRpcCodec2() 
        {
            var body1 = new byte[3] { 4, 5, 6 };
            var reqHeartBeat1 = new RequestHeartBeat() { MilliSeconds = 123 };
            var rpcMessage1 = new RpcMessage(reqHeartBeat1, body1);
            var buffer1 = rpcCodec2.Encode(allocator, rpcMessage1);
            var bufferLength1 = buffer1.ReadableBytes;

            var body2 = new byte[4] { 7, 8, 9, 10 };
            var reqHeartBeat2 = new RequestHeartBeat() { MilliSeconds = 34234234 };
            var rpcMessage2 = new RpcMessage(reqHeartBeat2, body2);
            var buffer2 = rpcCodec2.Encode(allocator, rpcMessage2);
            var bufferLength2 = buffer2.ReadableBytes;


            var buffer = allocator.Buffer();
            buffer.WriteBytes(buffer1);
            buffer.WriteBytes(buffer2);

            var (length1, typeName1, msg1) = rpcCodec2.Decode(buffer);
            RpcMessageEqual(rpcMessage1, bufferLength1, msg1 as RpcMessage, (int)length1);

            var (length2, typeName2, msg2) = rpcCodec2.Decode(buffer);
            RpcMessageEqual(rpcMessage2, bufferLength2, msg2 as RpcMessage, (int)length2);
        }
    }
}
