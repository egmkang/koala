using Abstractions.Network;

namespace Gateway.Handler
{
    public class GatewayPlayerSessionInfo
    {
        static byte[] Empty = new byte[0];

        public string AccountID = "";
        public string OpenID = "";
        public byte[] Token = Empty;
        public string ActorType = "";
        public string ActorID = "";
        public long DestServerID;
    }

    public static partial class GatewayExtensions
    {
        private const string KeyGatewaySessionInfo = "KeyGatewaySessionInfo";

        public static GatewayPlayerSessionInfo GetPlayerInfo(this IConnectionSessionInfo sessionInfo)
        {
            if (sessionInfo.States.TryGetValue(KeyGatewaySessionInfo, out var v))
            {
                var value = v as GatewayPlayerSessionInfo;
                if (value != null)
                    return value;
            }
            var info = new GatewayPlayerSessionInfo();
            sessionInfo.States.TryAdd(KeyGatewaySessionInfo, info);
            return info;
        }
    }
}
