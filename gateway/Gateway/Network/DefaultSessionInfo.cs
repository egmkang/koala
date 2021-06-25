using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway.Network
{
    public class DefaultSessionInfo : ISessionInfo
    {
        public DefaultSessionInfo(long sessionID, int uniqueServerID) 
        {
            this.SessionID = sessionID;
            this.UniqueServerID = uniqueServerID;
        }

        public long SessionID { get; private set; }
        public string OpenID { get; set; }
        public int ServerID { get; set; }
        public string ActorType { get;  set; }
        public string ActorID { get;  set; }
        public int UniqueServerID { get; private set; }
        public Dictionary<string, string> ExtraInfo { get; private set; } = new Dictionary<string, string>();
    }
}
