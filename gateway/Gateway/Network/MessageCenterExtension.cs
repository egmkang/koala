using Abstractions.Network;
using System;
using System.Collections.Generic;
using System.Text;

namespace Gateway.Network
{
    public static class MessageCenterExtension
    {
        public static void RegisterTypedMessageProc<T>(this IMessageCenter messageCenter, Action<InboundMessage> inboundMessageProc)
        {
            var fullName = typeof(T).FullName;
            if (string.IsNullOrEmpty(fullName)) 
            {
                return;
            }
            messageCenter.RegisterMessageProc(fullName, inboundMessageProc, false);
        }

        public static void RegisterTypedMessageProc<T>(this IMessageCenter messageCenter, Action<InboundMessage> inboundMessageProc, bool replace)
        {
            var fullName = typeof(T).FullName;
            if (string.IsNullOrEmpty(fullName)) 
            {
                return;
            }
            messageCenter.RegisterMessageProc(fullName, inboundMessageProc, replace);
        }
    }
}
