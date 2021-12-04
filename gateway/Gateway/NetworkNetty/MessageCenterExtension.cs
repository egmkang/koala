using Abstractions.Network;
using System;
using System.Collections.Generic;
using System.Text;

namespace Gateway.NetworkNetty
{
    public static class MessageCenterExtension
    {
        public static void RegisterTypedMessageProc<T>(this IMessageCenter messageCenter, Action<InboundMessage> inboundMessageProc)
        {
            var fullName = typeof(T).FullName;
            messageCenter.RegisterMessageProc(fullName, inboundMessageProc, false);
        }

        public static void RegisterTypedMessageProc<T>(this IMessageCenter messageCenter, Action<InboundMessage> inboundMessageProc, bool replace)
        {
            var fullName = typeof(T).FullName;
            messageCenter.RegisterMessageProc(fullName, inboundMessageProc, replace);
        }
    }
}
