using System;
using System.Collections.Concurrent;
using System.Text;
using Microsoft.Extensions.Logging;
using DotNetty.Transport.Channels;
using Abstractions.Network;

#nullable enable

namespace Gateway.Network
{
    public sealed class ConnectionManager : IConnectionManager
    {
        private readonly ConcurrentDictionary<long, WeakReference<IChannel>> channels = new ConcurrentDictionary<long, WeakReference<IChannel>>();
        private readonly ILogger logger;

        public ConnectionManager(ILoggerFactory loggerFactory)
        {
            logger = loggerFactory.CreateLogger("Network");
        }

        public void AddConnection(IChannel channel)
        {
            var info = channel.GetSessionInfo();
            if (!channels.TryAdd(info.SessionID, new WeakReference<IChannel>(channel)))
            {
                logger.LogError("ConnectionManager.AddConnection fail, SessionID:{0}", info.SessionID);
            }
            else 
            {
                logger.LogInformation("ConnectionManager.AddConnection, SessionID:{0}, Type:{1}", info.SessionID, info.ConnectionType);
            }
        }

        public IChannel? GetConnection(long sessionID)
        {
            channels.TryGetValue(sessionID, out var channel);
            if (channel == null) return null;
            channel.TryGetTarget(out var v);
            return v;
        }

        public void RemoveConnection(long sessionID)
        {
            channels.TryRemove(sessionID, out var _);
            logger.LogInformation("ConnectionManager.RemoveConnection, SessionID:{0}", sessionID);
        }
    }
}
