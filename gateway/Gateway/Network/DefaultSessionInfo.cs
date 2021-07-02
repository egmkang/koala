using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway.Network
{
    public class DefaultSessionInfo : ISessionInfo
    {
        public DefaultSessionInfo(long sessionID, long uniqueServerID) 
        {
            this.SessionID = sessionID;
            this.SessionServerID = uniqueServerID;
        }

        public bool IsClient { get; set; } = false;
        public byte[] Token { get; set; }
        public long DestServerID { get; set; }
        public long SessionID { get; private set; }
        public string OpenID { get; set; }
        public int GameServerID { get; set; }
        public string ActorType { get;  set; }
        public string ActorID { get;  set; }
        public long SessionServerID { get; private set; }
        public Dictionary<string, string> ExtraInfo { get; private set; } = new Dictionary<string, string>();
    }
}
