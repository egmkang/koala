using System;
using System.Collections.Generic;
using System.Text;
using DotNetty.Transport.Channels;

namespace Gateway.NetworkNetty
{
    public interface IMessageCenter
    {
        void RegsiterEvent(Action<IChannel> channelClosedProc,
            Action<OutboundMessage> failMessageProc);
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
        void RegisterUserMessageCallback(Func<string, string, InboundMessage, bool> fn);
        /// <summary>
        /// 收到了一个Actor用户消息, 需要塞到Actor的MailBox里面去顺序处理
        /// </summary>
        /// <param name="type">Actor的类型</param>
        /// <param name="actorID">Actor的ID</param>
        /// <param name="message">收到的消息</param>
        /// <returns>返回这个消息是否被接受了, 不接受的原因可能是内部报错, 或者Actor不在当前的host内</returns>
        bool OnReceiveUserMessage(string type, string actorID, InboundMessage message);
        void OnMessageFail(OutboundMessage message);
        void OnConnectionClosed(IChannel channel);
    }
}
