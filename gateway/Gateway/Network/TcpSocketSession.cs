using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Gateway.Handler;
using Gateway.Message;
using Gateway.Utils;
using Microsoft.AspNetCore.Connections;
using Microsoft.Extensions.Logging;

namespace Gateway.Network
{
    public class TcpSocketSession : ISession
    {
        private static readonly UnboundedChannelOptions Options = new UnboundedChannelOptions() 
        {
             SingleReader = true,
             SingleWriter = false,
        };
        private readonly ILogger logger;
        private readonly ConnectionContext context;
        private readonly ISessionInfo sessionInfo;
        private readonly IMessageCenter messageCenter;
        private readonly Channel<RpcMessage> outboundMessages = Channel.CreateUnbounded<RpcMessage>(Options);
        private readonly CancellationTokenSource cancellationTokenSource = new CancellationTokenSource();
        private readonly RpcMessageCodec codec = new RpcMessageCodec();

        public TcpSocketSession(ConnectionContext context, ISessionInfo sessionInfo, ILogger logger, IMessageCenter messageCenter)
        {
            this.context = context;
            this.logger = logger;
            this.messageCenter = messageCenter;
            this.sessionInfo = sessionInfo;
            this.RemoteAddress = this.context.RemoteEndPoint.ToString();
            this.LastMessageTime = Platform.GetMilliSeconds();
        }

        public long SessionID => this.sessionInfo.SessionID;

        public string RemoteAddress { get; private set; }

        public SessionType SessionType => SessionType.SessionType_Socket;

        public long LastMessageTime { get; set; }

        public ISessionInfo UserData => this.sessionInfo;

        public bool IsActive => !this.cancellationTokenSource.IsCancellationRequested;

        public async Task CloseAsync()
        {
            try
            {
                this.logger.LogInformation("TcpSocketSession Close, SessionID:{0}, RemoteAddress:{1}", this.SessionID, this.RemoteAddress);
                this.cancellationTokenSource.Cancel();
                await this.messageCenter.OnWebSocketClose(this).ConfigureAwait(false);
            }
            finally 
            {
                await this.context.DisposeAsync().ConfigureAwait(false);
            }
        }

        private async Task SendLoop()
        {
            var output = this.context.Transport.Output;
            var reader = this.outboundMessages.Reader;
            while (!this.cancellationTokenSource.IsCancellationRequested) 
            {
                if (!await reader.WaitToReadAsync(this.cancellationTokenSource.Token).ConfigureAwait(false))
                    continue;
                try
                {
                    while (reader.TryRead(out var msg))
                    {
                        this.codec.Encode(output, msg);
                    }
                    await output.FlushAsync().ConfigureAwait(false);
                }
                catch (Exception e)
                {
                    this.logger.LogError("TcpSocketSession SendLoop, SessionID:{0}, Exception:{1}", this.SessionID, e);
                    await this.CloseAsync().ConfigureAwait(false);
                }
            }
        }

        public async Task RecvLoop()
        {
            var input = this.context.Transport.Input;
            while (!this.cancellationTokenSource.IsCancellationRequested) 
            {
                var readResult = await input.ReadAsync();
                var buffer = readResult.Buffer;
                if (readResult.IsCanceled || readResult.IsCompleted) break;

                try 
                {
                    var len = 0;
                    if ((len = this.codec.Decode(buffer, out var message)) > 0)
                    {
                        input.AdvanceTo(buffer.Start, buffer.GetPosition(len));

                        await this.messageCenter.OnSocketMessage(this, message.Meta, message.Body).ConfigureAwait(false);
                    }
                }
                catch (Exception e) 
                {
                    this.logger.LogError("TcpSocketSession RecvMessage, SessionID:{0}, Exception:{1}", this.SessionID, e);
                    await this.CloseAsync().ConfigureAwait(false);
                }
            }
        }

        private static readonly Exception ErrorMessage = new Exception("Input Message Must Be RpcMessage");
        public async Task SendMessage(object msg)
        {
            var message = msg as RpcMessage;
            if (message == null) 
            {
                throw ErrorMessage;
            }
            if (!this.outboundMessages.Writer.TryWrite(message)) 
            {
                await this.outboundMessages.Writer.WriteAsync(message).ConfigureAwait(false);
            }
        }

        public async Task MainLoop()
        {
            await Task.WhenAll(this.RecvLoop(), this.SendLoop());
        }
    }
}
