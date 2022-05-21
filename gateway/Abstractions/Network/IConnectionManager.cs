using System;
using System.Collections.Generic;
using System.Text;
using DotNetty.Transport.Channels;

#nullable enable

namespace Abstractions.Network
{
    public interface IConnectionManager
    {
        void AddConnection(IChannel channel);

        void RemoveConnection(long sessionID);

        IChannel? GetConnection(long sessionID);
    }
}
