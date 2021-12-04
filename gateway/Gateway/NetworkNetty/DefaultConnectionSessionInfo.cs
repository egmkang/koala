using System;
using System.Collections.Generic;
using System.Net;
using System.Text;
using System.Collections.Concurrent;
using Microsoft.Extensions.Logging;
using DotNetty.Buffers;
using DotNetty.Transport.Channels;
using Gateway.Utils;
using Abstractions.Network;

namespace Gateway.NetworkNetty
{
    public sealed class DefaultConnectionSessionInfo : IConnectionSessionInfo
    {
        private readonly long sessionID;
        private long activeTime;
        private bool stop = false;
        private IPEndPoint address;
        private readonly ConcurrentQueue<OutboundMessage> inboundMessageQueue;
        private readonly ILogger logger;
        private readonly IMessageCenter messageCenter;
        private readonly IMessageCodec codec;
        private readonly SendingThreads sendingThreads;
        private readonly Dictionary<string, object> states = new Dictionary<string, object>();

        public DefaultConnectionSessionInfo(long sessionID,
                                            ILogger logger,
                                            IMessageCenter messageCenter,
                                            IMessageCodec codec,
                                            SendingThreads sendingThreads)
        {
            this.sessionID = sessionID;
            this.logger = logger;
            this.messageCenter = messageCenter;
            this.codec = codec;
            this.sendingThreads = sendingThreads;

            this.inboundMessageQueue = new ConcurrentQueue<OutboundMessage>();

            this.ActiveTime = Platform.GetMilliSeconds();
        }

        public long SessionID => sessionID;

        public long ActiveTime { get => activeTime; set => activeTime = value; }
        public IPEndPoint RemoteAddress { get => address; set => address = value; }
        public long ServerID { get; set; }
        public bool IsActive => !this.stop;
        public Dictionary<string, object> States => states;

        public int PutOutboundMessage(OutboundMessage msg)
        {
            if (this.stop) return 0;
            this.inboundMessageQueue.Enqueue(msg);
            this.sendingThreads.SendMessage(msg.DestConnection);
            return 1;
        }

        public void ShutDown() 
        {
            this.stop = true;
            this.inboundMessageQueue.Enqueue(OutboundMessage.Empty);
        }

        struct SafeReleaseByteBuffer : IDisposable
        {
            IByteBuffer buffer;
            public SafeReleaseByteBuffer(IByteBuffer buffer) 
            {
                this.buffer = buffer;
            }
            public void Dispose()
            {
                try { if (this.buffer != null) this.buffer.Release(); }
                catch { }
            }
        }

        public void SendMessagesBatch(IChannel channel)
        {
            if (this.stop) return;

            var allocator = channel.Allocator;
            var buffer = channel.Allocator.Buffer(1024);

            while (this.inboundMessageQueue.TryDequeue(out var message) && message.Inner != null) 
            {
                try
                {
                    //this.logger.LogTrace("Encoding Msg:{0}", message.Inner.GetType().Name);
                    var msg = this.codec.Encode(allocator, message.Inner);
                    using var _ = new SafeReleaseByteBuffer(msg);
                    buffer.WriteBytes(msg);
                }
                catch (Exception e) 
                {
                    logger.LogError("SendOutboundMessage Fail, SessionID:{0}, Exception:{1}",
                        this.sessionID, e);
                }
            }
            channel.WriteAndFlushAsync(buffer);
        }
    }
}
