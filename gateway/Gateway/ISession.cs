using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway
{
    public enum SessionType 
    {
        SessionType_Socket = 1,
        SessionType_WebSocket = 2,
        SessionType_Quic = 3,
    }

    public interface ISessionInfo 
    {
        long SessionID { get; }
        //这边是WebSocket的Session信息
        string OpenID { get; }
        int ServerID { get; }
        string ActorType { get; set; }
        string ActorID { get; set; }
        //这边是服务器内部Session的信息
        int UniqueServerID { get; }

        Dictionary<string, string> ExtraInfo { get; }
    }

    public interface ISession
    {
        long SessionID { get; }
        string RemoteAddress { get; }
        SessionType SessionType { get; }
        long LastMessageTime { get; set; }
        ISessionInfo UserData { get; }
        void Close();
        Task SendMessage(object msg);
    }
}
