using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;

namespace Gateway.NetworkNetty
{
    public interface IConnectionListener
    {
        void Init();
        Task BindAsync(int port, IMessageHandlerFactory factory);
        Task ShutdDownAsync();
    }
}
