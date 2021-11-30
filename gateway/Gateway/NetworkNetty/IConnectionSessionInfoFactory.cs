using System;
using System.Collections.Generic;
using System.Text;
using DotNetty.Buffers;

namespace Gateway.NetworkNetty
{
    public interface IConnectionSessionInfoFactory
    {
        IConnectionSessionInfo NewSessionInfo(IMessageHandlerFactory factory);
    }
}
