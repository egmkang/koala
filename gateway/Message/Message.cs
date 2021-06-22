using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace Gateway.Message
{
    public interface RpcMeta { }

    // token的bytes, 带在RPC PROTOCOL的body里面
    public class NotifyConnectionComming : RpcMeta
    {
        [JsonProperty("server_type")]
        public string ServiceType { get; set; }

        [JsonProperty("actor_id")]
        public string ActorId { get; set; }

        [JsonProperty("session_id")]
        public long SessionId { get; set; }

        [JsonProperty("token")]
        public byte[] Token { get; set; }
    }

    public class NotifyConnectionAborted : RpcMeta
    {
        [JsonProperty("session_id")]
        public long SessionId { get; set; }

        [JsonProperty("server_type")]
        public string ServiceType { get; set; }

        [JsonProperty("actor_id")]
        public string ActorId { get; set; }
    }

    public class RequestCloseConnection : RpcMeta
    {
        [JsonProperty("session_id")]
        public long SessionId { get; set; }

        [JsonProperty("server_type")]
        public string ServiceType { get; set; }
    }

    // message携带在RPC PROTOCOL的body里面
    public class NotifyNewMessage : RpcMeta
    {
        [JsonProperty("session_id")]
        public long SessionId { get; set; }

        [JsonProperty("server_type")]
        public string ServiceType { get; set; }

        [JsonProperty("actor_id")]
        public string ActorId { get; set; }
    }

    public class RequestSendMessageToPlayer : RpcMeta
    {
        [JsonProperty("session_id")]
        public long SessionId { get; set; }

        [JsonProperty("session_ids")]
        public long[] SessionIds { get; set; }
    }

    public class HeartBeatRequest : RpcMeta
    {
        [JsonProperty("milli_seconds")]
        public long MilliSeconds { get; set; }
    }

    public class HeartBeatResponse : RpcMeta
    {
        [JsonProperty("milli_seconds")]
        public long MilliSeconds { get; set; }
    }

}
