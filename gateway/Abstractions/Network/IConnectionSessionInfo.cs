using System;
using System.Collections.Generic;
using System.Net;
using System.Text;
using System.Threading.Channels;
using DotNetty.Transport.Channels;

namespace Abstractions.Network
{
    public enum ConnectionType 
    {
        None = 0,
        Socket = 1,
        WebSocket = 2,
    }

    public interface IConnectionSessionInfo
    {
        ConnectionType ConnectionType { get; set; }
        long SessionID { get; }
        long ServerID { get; set; }
        long ActiveTime { get; set; }
        IPEndPoint RemoteAddress { get; set; }
        bool IsActive { get; }
        Dictionary<string, object> States { get; }
        Action<IChannel> OnClosed { get; set; }
        Action<OutboundMessage> OnFail { get; set; }

        int PutOutboundMessage(OutboundMessage msg);
        void SendMessagesBatch(IChannel channel);
        void ShutDown();
    }
}
