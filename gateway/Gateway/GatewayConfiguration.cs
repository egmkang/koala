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
        /// 和Host集群通讯的端口, 对外不需要暴露
        /// </summary>
        public int ListenPort => Convert.ToInt32(this.ListenAddress.Split(':').Last());
        /// <summary>
        /// WebSocket的请求路径
        /// </summary>
        public string WebSocketPath { get; set; }
        /// <summary>
        /// 网关的地址
        /// </summary>
        public string GatewayAddress { get; set; }
        /// <summary>
        /// 后端实现认证的服务, 默认是IAccount
        /// </summary>
        public string AuthService { get; set; }
        /// <summary>
        /// 认证的私钥
        /// </summary>
        public string PrivateKey { get; set; }
        /// <summary>
        /// WebSocket收包频率限制
        /// 0表示不限制频率
        /// </summary>
        public int WebSocketRateLimit { get; set; }
        /// <summary>
        /// 是否禁用token校验
        /// </summary>
        public bool DisableTokenCheck { get; set; }

        public int GetGatewayWebSocketPort() 
        {
            if (this.GatewayAddress.IndexOf(':', this.GatewayAddress.IndexOf("://") + 3) < 0) 
            {
                return 80;
            }
            var sub = this.GatewayAddress.Substring(this.GatewayAddress.IndexOf(':', this.GatewayAddress.IndexOf("://") + 3) + 1);
            return Convert.ToInt32(sub.Split('/')[0]);
        }
        public string GetGatewayWebSocketPath() 
        {
            if (this.GatewayAddress.IndexOf('/', this.GatewayAddress.IndexOf("://") + 3) < 0) 
            {
                return "/";
            }
            var sub = this.GatewayAddress.Substring(this.GatewayAddress.IndexOf('/', this.GatewayAddress.IndexOf("://") + 3));
            return sub;
        }
    }
}
