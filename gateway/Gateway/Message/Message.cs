using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace Gateway.Message
{
    public class RpcMeta { }

    // token的bytes, 带在RPC PROTOCOL的body里面
    public class NotifyConnectionComming : RpcMeta
    {
        [JsonPropertyName("server_type")]
        public string ServiceType { get; set; }

        [JsonPropertyName("actor_id")]
        public string ActorId { get; set; }

        [JsonPropertyName("session_id")]
        public long SessionId { get; set; }

        [JsonPropertyName("token")]
        public byte[] Token { get; set; }
    }

    public class NotifyConnectionAborted : RpcMeta
    {
        [JsonPropertyName("session_id")]
        public long SessionId { get; set; }

        [JsonPropertyName("server_type")]
        public string ServiceType { get; set; }

        [JsonPropertyName("actor_id")]
        public string ActorId { get; set; }
    }

    public class RequestCloseConnection : RpcMeta
    {
        [JsonPropertyName("session_id")]
        public long SessionId { get; set; }

        [JsonPropertyName("server_type")]
        public string ServiceType { get; set; }
    }

    // message携带在RPC PROTOCOL的body里面
    public class NotifyNewMessage : RpcMeta
    {
        [JsonPropertyName("session_id")]
        public long SessionId { get; set; }

        [JsonPropertyName("server_type")]
        public string ServiceType { get; set; }

        [JsonPropertyName("actor_id")]
        public string ActorId { get; set; }
    }

    public class RequestSendMessageToPlayer : RpcMeta
    {
        [JsonPropertyName("session_id")]
        public long SessionId { get; set; }

        [JsonPropertyName("session_ids")]
        public long[] SessionIds { get; set; }
    }

    public class HeartBeatRequest : RpcMeta
    {
        [JsonPropertyName("milli_seconds")]
        public long MilliSeconds { get; set; }
    }

    public class HeartBeatResponse : RpcMeta
    {
        [JsonPropertyName("milli_seconds")]
        public long MilliSeconds { get; set; }
    }

}
