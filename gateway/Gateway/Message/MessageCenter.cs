using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Concurrent;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.DependencyInjection;
using DotNetty.Transport.Channels;
using Abstractions.Network;
using Gateway.Utils;
using Gateway.Network;

namespace Gateway.Message
{
    public sealed class MessageCenter : IMessageCenter
    {
        private readonly IServiceProvider serviceProvider;
        private readonly ILoggerFactory loggerFactory;
        private readonly ILogger logger;
        private readonly IConnectionManager connectionManager;
        private readonly Dictionary<string, Action<InboundMessage>> inboudMessageProc = new Dictionary<string, Action<InboundMessage>>();
        private readonly object mutex = new object();
        private readonly AtomicInt64 pendingProcessCounter = new AtomicInt64();
        private readonly ConcurrentQueue<Nullable<InboundMessage>> inboundMessages = new ConcurrentQueue<Nullable<InboundMessage>>();
        private readonly Thread messageThread;
        private volatile bool stop = false;
        private ClientConnectionPool? clientConnectionPool = null;

        private Action<InboundMessage> defaultInboundMessageProc = (_) => { }; 

        public MessageCenter(IServiceProvider serviceProvider,
                             ILoggerFactory loggerFactory,
                             IConnectionManager connectionManager) 
        {
            this.serviceProvider = serviceProvider;
            this.loggerFactory = loggerFactory;
            this.connectionManager = connectionManager;
            this.logger = this.loggerFactory.CreateLogger("MessageCenter");

            this.messageThread = new Thread(this.MessageLoop);
            this.messageThread.Name = "MessageProcess";
            this.messageThread.Start();
        }

        private void MessageLoop() 
        {
            while (!this.stop) 
            {
                lock (this.mutex)
                {
                    while (true)
                    {
                        var c = this.pendingProcessCounter.Load();
                        if (c == 0)
                        {
                            Monitor.Wait(this.mutex);
                            continue;
                        }
                        this.pendingProcessCounter.Add(-c);
                        break;
                    }
                }

                while (this.inboundMessages.TryDequeue(out var message) && message != null) 
                {
                    try
                    {
                        this.ProcessInboundMessage(message.Value);
                    }
                    catch (Exception e)
                    {
                        this.logger.LogError("MessageCenter Process InboundMessage, Exception:{0}, StackTrace:{1}", e, e.StackTrace?.ToString());
                    }
                }
            }
            this.logger.LogInformation("MessageCenter Exit");
        }

        public void StopAsync()
        {
            this.stop = true;
            this.inboundMessages.Enqueue(null);
        }

        public void OnConnectionClosed(IChannel channel)
        {
            var sessionInfo = channel.GetSessionInfo();
            this.connectionManager.RemoveConnection(sessionInfo.SessionID);
            try
            {
                if (sessionInfo.OnClosed != null) 
                {
                    sessionInfo.OnClosed(channel);
                }
            }
            catch (Exception e)
            {
                this.logger.LogError("MessageCenter OnConnectionClosed, ChannelID:{0}, Exception:{1}, StackTrace:{2}",
                    channel.GetSessionInfo().SessionID, e, e.StackTrace?.ToString());
            }
        }

        public void OnReceiveMessage(InboundMessage message)
        {
            if (this.logger.IsEnabled(LogLevel.Trace)) 
            {
                var sessionInfo = message.SourceConnection.GetSessionInfo();
                this.logger.LogTrace("MessageCenter.OnRecievedMessage, SessionID:{0}, MilliSeconds:{1}, Data:{2}",
                    sessionInfo.SessionID, message.MilliSeconds, message.Inner.ToString());
            }

            if (this.stop) return;

            this.inboundMessages.Enqueue(message);
            lock (this.mutex) 
            {
                this.pendingProcessCounter.Inc();
                Monitor.Pulse(this.mutex);
            }
        }

        public bool SendMessageToServer(long serverID, object message) 
        {
            if (this.clientConnectionPool == null) 
            {
                this.clientConnectionPool = this.serviceProvider.GetRequiredService<ClientConnectionPool>();
            }
            if (this.clientConnectionPool != null) 
            {
                var channel = this.clientConnectionPool.GetChannelByServerID(serverID);
                if (channel != null) 
                {
                    this.SendMessage(new OutboundMessage(channel, message));
                    return true;
                }
            }
            return false;
        }

        public void SendMessage(OutboundMessage message)
        {
            var session = message.DestConnection;
            var sessionInfo = message.DestConnection.GetSessionInfo();
            var size = 0;
            if ((size = sessionInfo.PutOutboundMessage(message)) > 1000)
            {
                this.logger.LogWarning("SessionID:{0}, SendingQueueCount:{1}",
                   sessionInfo.SessionID, size);
            }
        }

        public void RegisterDefaultMessageProc(Action<InboundMessage> inboundMessageProc)
        {
            this.defaultInboundMessageProc = inboundMessageProc;
            this.logger.LogInformation("RegisterMessageProc default proc");
        }

        public void RegisterMessageProc(string messageName, Action<InboundMessage> inboundMessageProc, bool replace)
        {
            if (string.IsNullOrEmpty(messageName)) 
            {
                this.logger.LogError("RegisterMessageProc, MessageName is null or empty");
                return;
            }
            if (replace) 
            {
                this.inboudMessageProc.Remove(messageName);
            }
            if (!this.inboudMessageProc.TryAdd(messageName, inboundMessageProc))
            {
                this.logger.LogError("RegisterMessageProc, MessageName:{0} exists", messageName);
                return;
            }
            this.logger.LogInformation("RegisterMessageProc, MessageName:{0}", messageName);
        }

        private void ProcessInboundMessage(InboundMessage message) 
        {
            if (this.defaultInboundMessageProc == null) 
            {
                this.logger.LogError("ProcessInboundMessage but DefaultInboundMessageProc is null");
                return;
            }
            if (string.IsNullOrEmpty(message.MessageName)) 
            {
                this.defaultInboundMessageProc(message);
                return;
            }
            if (this.logger.IsEnabled(LogLevel.Debug)) 
            {
                if (message.MessageName != "RequestHeartBeat" &&
                    message.MessageName != "ResponseHeartBeat") 
                {
                    this.logger.LogDebug("ProcessMessage, MessageName:{0}", message.MessageName);
                }
            }
            if (this.inboudMessageProc.TryGetValue(message.MessageName, out var proc))
            {
                proc(message);
            }
            else 
            {
                this.defaultInboundMessageProc(message);
            }
        }
    }
}
