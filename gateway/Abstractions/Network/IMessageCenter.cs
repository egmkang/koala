using System;
using System.Collections.Generic;
using System.Text;
using DotNetty.Transport.Channels;

namespace Abstractions.Network
{
    public interface IMessageCenter
    {
        /// <summary>
        /// 默认的消息处理, 如果该消息没有任何人处理, 那么就会被该函数处理
        /// </summary>
        /// <param name="inboundMessageProc">消息处理函数</param>
        void RegisterDefaultMessageProc(Action<InboundMessage> inboundMessageProc);
        /// <summary>
        /// 注册消息的回调函数
        /// </summary>
        /// <param name="messageName">消息的名字</param>
        /// <param name="inboundMessage">需要被处理的消息</param>
        /// <param name="replace">是否需要替换实现</param>
        void RegisterMessageProc(string messageName, Action<InboundMessage> inboundMessageProc, bool replace);
        /// <summary>
        /// 发送消息给指定IChannel
        /// </summary>
        /// <param name="message">消息</param>
        void SendMessage(OutboundMessage message);
        /// <summary>
        /// 发送消息给指定的服务器
        /// </summary>
        /// <param name="serverID">服务器唯一ID, 集群内唯一</param>
        /// <param name="message">消息</param>
        /// <returns>是否发Push到指定服务器的消息队列里面</returns>
        bool SendMessageToServer(long serverID, object message);

        void OnReceiveMessage(InboundMessage message);
        void OnConnectionClosed(IChannel channel);
    }
}
