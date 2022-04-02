using Abstractions.Network;

namespace Gateway.Handler
{
    public class GatewayPlayerSessionInfo
    {
        public string AccountID;
        public string OpenID;
        public byte[] Token;
        public string ActorType;
        public string ActorID;
        public long DestServerID;
    }

    public static partial class GatewayExtensions
    {
        private const string KeyGatewaySessionInfo = "KeyGatewaySessionInfo";

        public static GatewayPlayerSessionInfo GetPlayerInfo(this IConnectionSessionInfo sessionInfo)
        {
            if (sessionInfo.States.TryGetValue(KeyGatewaySessionInfo, out var v))
            {
                return v as GatewayPlayerSessionInfo;
            }
            var info = new GatewayPlayerSessionInfo();
            sessionInfo.States.TryAdd(KeyGatewaySessionInfo, info);
            return info;
        }
    }
}
