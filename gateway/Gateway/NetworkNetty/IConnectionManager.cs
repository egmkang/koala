using System;
using System.Collections.Generic;
using System.Text;
using DotNetty.Transport.Channels;

namespace Gateway.NetworkNetty
{
    public interface IConnectionManager
    {
        void AddConnection(IChannel channel);

        void RemoveConnection(IChannel channel);

        IChannel GetConnection(long sessionID);
    }
}
