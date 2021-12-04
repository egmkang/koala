using System;
using System.Text.Json;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Text.Json.Serialization;

namespace Abstractions.Placement
{
    /// <summary>
    /// PD服务器上, Actor宿主服务器的信息
    /// </summary>
    public class PlacementActorHostInfo
    {
        /// <summary>
        /// 服务器唯一ID
        /// </summary>
        [JsonPropertyName("server_id")]
        public long ServerID { get; set; }
        /// <summary>
        /// 租约
        /// </summary>
        [JsonPropertyName("lease_id")]
        public long LeaseID { get; set; }
        /// <summary>
        /// 服务器的负载(运行时也就只有负载可变, 其他信息都不允许发生变化)
        /// </summary>
        [JsonPropertyName("load")]
        public long Load { get; set; }
        /// <summary>
        /// 服务器启动时间, 相对于UTC的毫秒数
        /// </summary>
        [JsonPropertyName("start_time")]
        public long StartTime { get; set; }
        /// <summary>
        /// 服务器的生存期
        /// </summary>
        [JsonPropertyName("ttl")]
        public long TTL { get; set; }
        /// <summary>
        /// 服务器的地址
        /// </summary>
        [JsonPropertyName("address")]
        public string Address { get; set; }
        /// <summary>
        /// 服务器能提供的Actor对象类型, 即服务能力
        /// </summary>
        [JsonPropertyName("services")]
        public Dictionary<string, string> Services { get; set; }
        /// <summary>
        /// 服务的描述信息
        /// </summary>
        [JsonPropertyName("desc")]
        public string Desc { get; set; }
        /// <summary>
        /// 服务器的额外属性, 用来表示网关等信息
        /// </summary>
        [JsonPropertyName("labels")]
        public Dictionary<string, string> Labels { get; set; }
    }

    /// <summary>
    /// PD上最近发生的事件
    /// </summary>
    public class PlacementEvents
    {
        /// <summary>
        /// 事件的事件
        /// </summary>
        [JsonPropertyName("time")]
        public long Time { get; set; }
        /// <summary>
        /// 增加的服务器ID
        /// </summary>
        [JsonPropertyName("add")]
        public List<long> Add { get; set; }
        /// <summary>
        /// 删除的服务器ID
        /// </summary>
        [JsonPropertyName("remove")]
        public List<long> Remove { get; set; }
    }

    /// <summary>
    /// 服务器续约返回
    /// </summary>
    public class PlacementKeepAliveResponse
    {
        /// <summary>
        /// 每次续约PD会将所有的服务器信息下发, 该framework所能处理的集群规模, 也就是百十来台, 所以将所有服务器下发没有问题
        /// </summary>
        [JsonPropertyName("hosts")]
        public Dictionary<long, PlacementActorHostInfo> Hosts { get; set; }
        /// <summary>
        /// 服务器最近的事件(增减和删除)
        /// </summary>
        [JsonPropertyName("events")]
        public List<PlacementEvents> Events { get; set; }
    }

    /// <summary>
    /// PD上对于Actor定位的请求
    /// </summary>
    public class PlacementFindActorPositionRequest
    {
        /// <summary>
        /// Actor的接口类型, PD里面有实现的类型
        /// </summary>
        [JsonPropertyName("actor_type")]
        public string ActorType { get; set; }
        /// <summary>
        /// Actor的ID, 在该ActorType下必须唯一
        /// </summary>
        [JsonPropertyName("actor_id")]
        public string ActorID { get; set; }
        /// <summary>
        /// Actor的生命周期, 通常为0, 那么Actor的宿主挂掉之后, PD会寻求再次分配新的位置
        /// 不为0时, 那么Actor的宿主挂掉之后, PD不会再次分配新的位置. 通常用来做一次性定位, 比如一场战斗, 战斗服务器挂掉后很难恢复.
        /// </summary>
        [JsonPropertyName("ttl")]
        public long TTL { get; set; }
    }

    /// <summary>
    /// PD对Actor定位的返回
    /// </summary>
    public class PlacementFindActorPositionResponse
    {
        /// <summary>
        /// Actor的类型, 参见ActorType
        /// </summary>
        [JsonPropertyName("actor_type")]
        public string ActorType { get; set; }
        /// <summary>
        /// ActorType类型下唯一的ID
        /// </summary>
        [JsonPropertyName("actor_id")]
        public string ActorID { get; set; }
        /// <summary>
        /// 生存期
        /// </summary>
        [JsonPropertyName("ttl")]
        public long TTL { get; set; }
        /// <summary>
        /// Actor分配的时间
        /// </summary>
        [JsonPropertyName("create_time")]
        public long CreateTime { get; set; }
        /// <summary>
        /// 宿主的唯一ID
        /// </summary>
        [JsonPropertyName("server_id")]
        public long ServerID { get; set; }
        /// <summary>
        /// 宿主的地址
        /// </summary>
        [JsonPropertyName("server_address")]
        public string ServerAddress { get; set; }
    }

    public class PlacementVersionInfo
    {
        [JsonPropertyName("version")]
        public string Version { get; set; }
        [JsonPropertyName("last_heart_beat_time")]
        public long LastHeartBeatTime { get; set; }
    }

    public interface IPlacement
    {
        /// <summary>
        /// 设置PlacementDriver服务器的信息
        /// </summary>
        /// <param name="address">PD服务器的地址</param>
        void SetPlacementServerInfo(string address);

        /// <summary>
        /// 生成一个新的服务器ID, 服务器每次启动的时候都需要向PD去申请新的ID
        /// </summary>
        /// <returns>返回新的唯一ID</returns>
        Task<long> GenerateServerIDAsync();
        /// <summary>
        /// 获取一个新的ID, 可以提供比较频繁的调用
        /// </summary>
        /// <param name="sequenceType">类型</param>
        /// <param name="step">步长, 内部一次申请步长个ID, 缓冲起来, 提高性能用的参数</param>
        /// <returns>返回一个SequenceID</returns>
        Task<long> GenerateNewSequenceAsync(string sequenceType, int step);
        /// <summary>
        /// 生成一个新的写入Token, 用来做Actor写入权限的判断
        /// </summary>
        /// <returns>生成新的Token</returns>
        Task<long> GenerateNewTokenAsync();
        /// <summary>
        /// 注册当前服务器到PD里面去
        /// </summary>
        /// <returns>返回租约</returns>
        Task<long> RegisterServerAsync(PlacementActorHostInfo info);
        /// <summary>
        /// 给当前服务器续约, 维持其生命
        /// </summary>
        /// <param name="serverID">服务器ID</param>
        /// <param name="leaseID">租约ID</param>
        /// <param name="load">服务器当前的负载</param>
        /// <returns>返回PD上面最新的事件</returns>
        Task<PlacementKeepAliveResponse> KeepAliveServerAsync(long serverID, long leaseID, long load);
        /// <summary>
        /// 在内存中找Actor所在的服务器信息
        /// </summary>
        /// <param name="request">actor定位所需要的信息</param>
        /// <returns>Actor所在的服务器信息</returns>
        PlacementFindActorPositionResponse FindActorPositionInCache(PlacementFindActorPositionRequest request);
        /// <summary>
        /// 找到Actor所在的服务器信息
        /// </summary>
        /// <param name="request">actor定位所需要的信息</param>
        /// <returns>Actor所在的目标服务器信息</returns>
        Task<PlacementFindActorPositionResponse> FindActorPositonAsync(PlacementFindActorPositionRequest request);
        /// <summary>
        /// 清空Actor的位置缓存
        /// </summary>
        /// <param name="request">actor信息</param>
        void ClearActorPositionCache(PlacementFindActorPositionRequest request);
        /// <summary>
        /// 获取版本信息
        /// </summary>
        /// <returns>返回版本信息的字符串</returns>
        Task<PlacementVersionInfo> GetVersionAsync();
        /// <summary>
        /// 获取当前服务器的信息
        /// </summary>
        long CurrentServerID { get; }

        /// <summary>
        /// 获取服务器列表变动事件
        /// </summary>
        /// <param name="onAddServer">添加新的服务器</param>
        /// <param name="onRemoveServer">删除老的服务器</param>
        /// <param name="onServerOffline">服务器即将做下线处理</param>
        void RegisterServerChangedEvent(Action<PlacementActorHostInfo> onAddServer,
                                        Action<PlacementActorHostInfo> onRemoveServer,
                                        Action<PlacementActorHostInfo> onServerOffline);
        /// <summary>
        /// 设置服务器的负载, 0表示无负载, 数字越大表示负载越大, -1表示服务器将要下线
        /// </summary>
        /// <param name="load">负载</param>
        void SetServerLoad(long load);
        /// <summary>
        /// 开启轮训续约的异步任务
        /// </summary>
        Task StartPullingAsync();
        /// <summary>
        /// 停止轮训续约
        /// </summary>
        Task StopPullingAsync();

        /// <summary>
        /// 碰到致命错误
        /// </summary>
        /// <param name="fn">回调</param>
        void OnException(Action<Exception> fn);
    }

    public class PlacementException : Exception
    {
        public PlacementException(int code, string message) : base(message)
        {
            this.Code = code;
        }

        public int Code { get; set; }
    }
}
