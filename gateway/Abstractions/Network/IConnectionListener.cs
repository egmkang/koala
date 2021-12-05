using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;

namespace Abstractions.Network
{
    public interface IConnectionListener
    {
        void Init();
        Task BindAsync(int port, IMessageHandlerFactory factory);
        Task BindWebSocketAsync(int port, string websocketPath, IMessageHandlerFactory factory);
        Task ShutdDownAsync();
    }
}
