using System;
using System.Collections.Generic;
using System.Net;
using System.Text;
using System.Threading.Channels;
using DotNetty.Transport.Channels;

namespace Gateway.NetworkNetty
{
    public interface IConnectionSessionInfo
    {
        long SessionID { get; }
        long ServerID { get; set; }
        long ActiveTime { get; set; }
        IPEndPoint RemoteAddress { get; set; }
        bool IsActive { get; }
        Dictionary<string, object> States { get; }

        int PutOutboundMessage(OutboundMessage msg);
        void SendMessagesBatch(IChannel channel);
        void ShutDown();
    }
}
