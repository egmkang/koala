using System;
using System.Buffers;
using System.Collections.Generic;
using System.Linq;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Gateway.Utils;

namespace Gateway.Network
{
    public class WebSocketSession : ISession
    {
        private static readonly UnboundedChannelOptions Options = new UnboundedChannelOptions() 
        {
             SingleReader = true,
             SingleWriter = false,
        };
        private const int RecvBufferSize = 32 * 1024;
        private readonly WebSocket webSocket;
        private readonly ILogger logger;
        private readonly Channel<byte[]> outboundMessages = Channel.CreateUnbounded<byte[]>(Options);
        private readonly CancellationTokenSource cancellationTokenSource = new CancellationTokenSource();
        private readonly IMessageCenter messageCenter;
        private readonly DefaultSessionInfo sessionInfo;

        public WebSocketSession(long sessionID, 
                                WebSocket webSocket, 
                                string address,
                                ILogger logger, 
                                IMessageCenter messageCenter) 
        {
            this.SessionID = sessionID;
            this.webSocket = webSocket;
            this.RemoteAddress = address;
            this.logger = logger;
            this.messageCenter = messageCenter;
            this.LastMessageTime = Platform.GetMilliSeconds();
            this.sessionInfo = new DefaultSessionInfo(sessionID, 0);
        }

        public void Close()
        {
            try
            {
                this.logger.LogInformation("WebSocket:{0} Close, RemoteAddress:{1}", this.SessionID, this.RemoteAddress);
                this.cancellationTokenSource.Cancel();
                _ = this.webSocket.CloseAsync(WebSocketCloseStatus.Empty, "", CancellationToken.None);
            }
            finally
            {
                this.messageCenter.OnWebSocketClose(this);
            }
        }

        public long SessionID { get; private set; }
        public string RemoteAddress { get; private set; }
        public SessionType SessionType => SessionType.SessionType_WebSocket;
        public long LastMessageTime { get; set; }
        ISessionInfo ISession.UserData => sessionInfo;

        public async Task SendMessage(object msg)
        {
            if (!this.outboundMessages.Writer.TryWrite(msg as byte[])) 
            {
                await this.outboundMessages.Writer.WriteAsync(msg as byte[]).ConfigureAwait(false);
            }
        }

        public async Task SendLoop() 
        {
            var reader = this.outboundMessages.Reader;
            while (!this.cancellationTokenSource.IsCancellationRequested) 
            {
                if (!await reader.WaitToReadAsync(this.cancellationTokenSource.Token).ConfigureAwait(false))
                    continue;
                while (reader.TryRead(out var msg))
                {
                    await this.webSocket.SendAsync(msg, WebSocketMessageType.Binary, true, CancellationToken.None).ConfigureAwait(false);
                }
            }
        }

        public async Task RecvLoop()
        {
            _ = this.SendLoop();
            using (var buffer = MemoryPool<byte>.Shared.Rent(RecvBufferSize))
            {
                var memory = buffer.Memory;
                while (!this.cancellationTokenSource.IsCancellationRequested)
                {
                    var result = await this.webSocket.ReceiveAsync(memory, this.cancellationTokenSource.Token).ConfigureAwait(false);
                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        this.Close();
                        break;
                    }
                    this.messageCenter.OnWebSocketMessage(this, memory, result.Count);
                }
            }
        }
    }
}
