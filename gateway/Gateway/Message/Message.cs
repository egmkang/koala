using System.Text.Json.Serialization;

namespace Gateway.Message
{
    public class RpcMeta { }

    public class RequestAccountLogin : RpcMeta 
    {
        [JsonPropertyName("open_id")]
        public string OpenID { get; set; }
        [JsonPropertyName("server_id")]
        public long ServerID { get; set; }
        [JsonPropertyName("session_id")]
        public long SessionID { get; set; }
    }

    public class ResponseAccountLogin : RpcMeta 
    {
        [JsonPropertyName("session_id")]
        public long SessionID { get; set; }
        [JsonPropertyName("actor_type")]
        public string ActorType { get; set; }
        [JsonPropertyName("actor_id")]
        public string ActorID { get; set; }
    }

    // token的bytes, 带在RPC PROTOCOL的body里面
    public class NotifyNewActorSession : RpcMeta
    {
        [JsonPropertyName("actor_type")]
        public string ActorType { get; set; }
        [JsonPropertyName("actor_id")]
        public string ActorID { get; set; }
        [JsonPropertyName("session_id")]
        public long SessionID { get; set; }
        [JsonPropertyName("open_id")]
        public string OpenID { get; set; }
        [JsonPropertyName("server_id")]
        public long ServerID { get; set; }
    }

    public class NotifyActorSessionAborted : RpcMeta
    {
        [JsonPropertyName("session_id")]
        public long SessionID { get; set; }

        [JsonPropertyName("actor_type")]
        public string ActorType { get; set; }

        [JsonPropertyName("actor_id")]
        public string ActorID { get; set; }
    }

    public class RequestCloseSession : RpcMeta
    {
        [JsonPropertyName("session_id")]
        public long SessionID { get; set; }

        [JsonPropertyName("actor_type")]
        public string ActorType { get; set; }
    }

    // message携带在RPC PROTOCOL的body里面
    public class NotifyNewActorMessage : RpcMeta
    {
        [JsonPropertyName("session_id")]
        public long SessionId { get; set; }

        [JsonPropertyName("actor_type")]
        public string ActorType { get; set; }

        [JsonPropertyName("actor_id")]
        public string ActorID { get; set; }
        [JsonPropertyName("trace")]
        public string Trace { get; set; }
    }

    // 要发送的消息携带在Body里面
    public class RequestSendMessageToSession : RpcMeta
    {
        [JsonPropertyName("session_id")]
        public long SessionId { get; set; }

        [JsonPropertyName("session_ids")]
        public long[] SessionIds { get; set; }
    }

    public class RequestHeartBeat : RpcMeta
    {
        [JsonPropertyName("milli_seconds")]
        public long MilliSeconds { get; set; }
    }

    public class ResponseHeartBeat : RpcMeta
    {
        [JsonPropertyName("milli_seconds")]
        public long MilliSeconds { get; set; }
    }
}
