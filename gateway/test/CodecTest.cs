using Gateway.Message;
using System;
using System.Buffers;
using Microsoft.VisualStudio.TestTools.UnitTesting;


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
            var req = new HeartBeatRequest() { MilliSeconds = 123 };
            var rpcMessage = new RpcMessage(req, null);

            var (memory, size) = rpcCodec.Encode(new MockBufferWriter(), rpcMessage);

            var messageSize = rpcCodec.Decode(new ReadOnlySequence<byte>(memory).Slice(0, size), out var decodedMessage);

            RpcMessageEqual(rpcMessage, size, decodedMessage, messageSize);
        }
        [TestMethod]
        public void TestRpcCodecWithBody()
        {
            var inputBody = new byte[3] { 1, 2, 3 };
            var req = new HeartBeatRequest() { MilliSeconds = 456 };
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
            Assert.AreEqual((m1.Meta as HeartBeatRequest).MilliSeconds, (m2.Meta as HeartBeatRequest).MilliSeconds);
        }

        [TestMethod]
        public void TestMultiMessagesRpcCodec() 
        {
            var body1 = new byte[3] { 4, 5, 6 };
            var reqHeartBeat1 = new HeartBeatRequest() { MilliSeconds = 123 };
            var rpcMessage1 = new RpcMessage(reqHeartBeat1, body1);
            var (memory1, size1) = rpcCodec.Encode(new MockBufferWriter(), rpcMessage1);

            var body2 = new byte[4] { 7, 8, 9, 10 };
            var reqHeartBeat2 = new HeartBeatRequest() { MilliSeconds = 34234234 };
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
    }
}
