using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway
{
    public class MessageCenter : IMessageCenter
    {
        private readonly IServiceProvider serviceProvider;
        private readonly SessionManager sessionManager;

        public MessageCenter(IServiceProvider serviceProvider, SessionManager sessionManager) 
        {
            this.serviceProvider = serviceProvider;
            this.sessionManager = sessionManager;
        }

        public void OnWebSocketClose(ISession session)
        {
            this.sessionManager.RemoveSession(session.SessionID);
            // TODO
            // 发送消息给Actor
        }

        public void OnWebSocketMessage(ISession session, Memory<byte> memory, int size)
        {
            var sessionInfo = session.UserData;
            if (string.IsNullOrEmpty(sessionInfo.OpenID))
            {
            }
            else 
            {
                //TODO
            }
        }

        public void RegisteEvent(OnWebSocketMessage onWebSocketMessage, OnWebSocketClose onWebSocketClose)
        {
            throw new NotImplementedException();
        }
    }
}
