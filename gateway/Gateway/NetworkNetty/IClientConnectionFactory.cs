using System;
using System.Collections.Generic;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using DotNetty.Transport.Channels;

namespace Gateway.NetworkNetty
{
    public interface IClientConnectionFactory
    {
        void Init();
        Task<IChannel> ConnectAsync(EndPoint address, IMessageHandlerFactory factory);
        Task ShutdDownAsync();
    }
}
