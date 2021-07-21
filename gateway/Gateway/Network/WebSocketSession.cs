﻿using System;
using System.Buffers;
using System.Collections.Generic;
using System.Linq;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Gateway.Utils;
using Gateway.Message;
using Gateway.Handler;

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
        private readonly ISessionInfo sessionInfo;

        public WebSocketSession(WebSocket webSocket, 
                                string address,
                                ILogger logger, 
                                IMessageCenter messageCenter,
                                ISessionInfo sessionInfo) 
        {
            this.webSocket = webSocket;
            this.RemoteAddress = address;
            this.logger = logger;
            this.messageCenter = messageCenter;
            this.LastMessageTime = Platform.GetMilliSeconds();
            this.sessionInfo = sessionInfo;
        }

        public bool IsActive => !this.cancellationTokenSource.IsCancellationRequested;

        public async Task CloseAsync()
        {
            try
            {
                if (this.cancellationTokenSource.IsCancellationRequested)
                    return;
                this.cancellationTokenSource.Cancel();

                this.logger.LogInformation("WebSocketSession:{0} Close, RemoteAddress:{1}", this.SessionID, this.RemoteAddress);
                await this.webSocket.CloseAsync(WebSocketCloseStatus.Empty, "", CancellationToken.None).ConfigureAwait(false);
            }
            catch { }
            finally
            {
                await this.messageCenter.OnWebSocketClose(this).ConfigureAwait(false);
            }
        }

        public long SessionID => this.sessionInfo.SessionID;
        public string RemoteAddress { get; private set; }
        public SessionType SessionType => SessionType.SessionType_WebSocket;
        public long LastMessageTime { get; set; }
        ISessionInfo ISession.UserData => sessionInfo;

        private static readonly Exception ErrorMessage = new Exception("Input Message Must Be byte[]");
        public async Task SendMessage(object msg)
        {
            var message = msg as byte[];
            if (message == null)
            {
                throw ErrorMessage;
            }
            if (!this.outboundMessages.Writer.TryWrite(message)) 
            {
                await this.outboundMessages.Writer.WriteAsync(message).ConfigureAwait(false);
            }
        }

        public async Task SendLoop()
        {
            var reader = this.outboundMessages.Reader;
            while (!this.cancellationTokenSource.IsCancellationRequested)
            {
                if (!await reader.WaitToReadAsync(this.cancellationTokenSource.Token).ConfigureAwait(false))
                    continue;
                try
                {
                    while (reader.TryRead(out var msg))
                    {
                        await this.webSocket.SendAsync(msg, WebSocketMessageType.Binary, true, CancellationToken.None).ConfigureAwait(false);
                    }
                }
                catch (Exception e)
                {
                    this.logger.LogError("WebSocketSession SendLoop, SessionID:{0}, Exception:{1}", this.SessionID, e);
                    await this.CloseAsync().ConfigureAwait(false);
                    break;
                }
            }
        }

        public async Task RecvLoop()
        {
            using (var buffer = MemoryPool<byte>.Shared.Rent(RecvBufferSize))
            {
                var memory = buffer.Memory;
                var rateLimit = new WebSocketRateLimit();

                while (!this.cancellationTokenSource.IsCancellationRequested)
                {
                    try
                    {
                        var result = await this.webSocket.ReceiveAsync(memory, this.cancellationTokenSource.Token).ConfigureAwait(false);
                        if (result.MessageType == WebSocketMessageType.Close)
                        {
                            this.logger.LogInformation("WebSocketSession, SessionID:{0} Receive Close Message", this.SessionID);
                            await this.CloseAsync().ConfigureAwait(false);
                            break;
                        }
                        if (rateLimit.Inc() > WebSocketRateLimit.Limit) 
                        {
                            this.logger.LogError("WebSocketSession RecvLoop, SessionID:{0} WebSocketRateLimit:{1}/{2}", 
                                                this.SessionID, rateLimit.GetCurrentCount(), WebSocketRateLimit.Limit);
                            await this.CloseAsync().ConfigureAwait(false);
                            break;
                        } 
                        await this.messageCenter.OnWebSocketMessage(this, memory, result.Count).ConfigureAwait(false);
                    }
                    catch (WebSocketException e) 
                    {
                        this.logger.LogWarning("WebSocketSession RecvLoop, SessionID:{0} WebSocketException:{1}", this.SessionID, e);
                        await this.CloseAsync().ConfigureAwait(false);
                        break;
                    }
                    catch (Exception e)
                    {
                        this.logger.LogError("WebSocketSession RecvLoop, SessionID:{0} Exception:{1}", this.SessionID, e);
                        await this.CloseAsync().ConfigureAwait(false);
                        break;
                    }
                }
            }
        }

        public async Task MainLoop()
        {
            try
            {
                await Task.WhenAll(this.RecvLoop(), this.SendLoop()).ConfigureAwait(false);
            }
            catch { }
        }
    }
}
