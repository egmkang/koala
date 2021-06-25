using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway
{
    public delegate void OnWebSocketMessage(ISession session, Memory<byte> memory, int size);
    public delegate void OnWebSocketClose(ISession session);

    public interface IMessageCenter
    {
        void RegisteEvent(OnWebSocketMessage onWebSocketMessage, OnWebSocketClose onWebSocketClose);

        void OnWebSocketClose(ISession session);
        void OnWebSocketMessage(ISession session, Memory<byte> memory, int size);
    }
}
