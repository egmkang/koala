using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway
{
    public class GatewayConfiguration
    {
        /// <summary>
        /// PD服务器的地址
        /// </summary>
        public string PlacementDriverAddress { get; set; }
        /// <summary>
        /// 跟PD续约的间隔
        /// </summary>
        public int KeepAliveInterval { get; set; }
        /// <summary>
        /// 和Host集群通讯的端口, 对外不需要暴露
        /// </summary>
        public string ListenAddress { get; set; }
        /// <summary>
        /// WebSocket的请求路径
        /// </summary>
        public string WebSocketPath { get; set; }
        /// <summary>
        /// 网关的地址
        /// </summary>
        public string GatewayAddress { get; set; }
    }
}
