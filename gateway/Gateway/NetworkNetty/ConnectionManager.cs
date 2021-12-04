using System;
using System.Collections.Concurrent;
using System.Text;
using Microsoft.Extensions.Logging;
using DotNetty.Transport.Channels;
using Abstractions.Network;

namespace Gateway.NetworkNetty
{
    public sealed class ConnectionManager : IConnectionManager
    {
        private readonly ConcurrentDictionary<long, IChannel> channels = new ConcurrentDictionary<long, IChannel>();
        private readonly ILogger logger;

        public ConnectionManager(ILoggerFactory loggerFactory)
        {
            logger = loggerFactory.CreateLogger("Network");
        }

        public void AddConnection(IChannel channel)
        {
            var info = channel.GetSessionInfo();
            if (!channels.TryAdd(info.SessionID, channel)) 
            {
                logger.LogError("ConnectionManager.AddConnection fail, SessionID:{0}", info.SessionID);
            }
        }

        public IChannel GetConnection(long sessionID)
        {
            channels.TryGetValue(sessionID, out var channel);
            return channel;
        }

        public void RemoveConnection(IChannel channel)
        {
            channels.TryRemove(channel.GetSessionInfo().SessionID, out var _);
        }
    }
}
