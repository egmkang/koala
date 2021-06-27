using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Gateway.Message;

namespace Gateway
{
    public interface IMessageCenter
    {
        Task OnWebSocketClose(ISession session);
        Task OnWebSocketLoginMessage(ISession session, string openID, int serverID, Memory<byte> memory, int size);
        Task OnWebSocketMessage(ISession session, Memory<byte> memory, int size);
        Task OnSocketClose(ISession session);
        Task OnSocketMessage(ISession session, RpcMeta rpcMeta, byte[] body);
        Task SendMessageToSession(long sessionID, object msg);
        Task SendMessageToServer(long serverID, object msg);
    }
}
