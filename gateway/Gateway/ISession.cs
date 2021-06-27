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
        byte[] Token { get; set; }
        //这边是WebSocket的Session信息
        string OpenID { get; set; }
        //游戏服务器ID
        int GameServerID { get; set; }
        /// <summary>
        /// 目标Actor的类型
        /// </summary>
        string ActorType { get; set; }
        /// <summary>
        /// 目标Actor的唯一ID
        /// </summary>
        string ActorID { get; set; }
        /// <summary>
        /// 消息转发给哪个服务器
        /// </summary>
        long DestServerID { get; set; }
        /// <summary>
        /// 服务器的唯一ID, 通过PD获取到的
        /// </summary>
        long UniqueServerID { get; }

        Dictionary<string, string> ExtraInfo { get; }
    }

    public interface ISession
    {
        long SessionID { get; }
        string RemoteAddress { get; }
        SessionType SessionType { get; }
        long LastMessageTime { get; set; }
        ISessionInfo UserData { get; }
        bool IsActive { get; }
        Task RecvLoop();
        Task CloseAsync();
        Task SendMessage(object msg);
    }
}
