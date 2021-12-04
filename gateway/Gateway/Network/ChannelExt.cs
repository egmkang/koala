using System;
using System.Collections.Generic;
using System.Net;
using System.Text;
using Abstractions.Network;
using DotNetty.Common.Utilities;
using DotNetty.Transport.Channels;

namespace Gateway.Network
{
    public static class ChannelExt
    {
        private const string SessionInfoKey = "SESSIONINFO";

        public static readonly AttributeKey<IConnectionSessionInfo> SESSION_INFO = AttributeKey<IConnectionSessionInfo>.ValueOf(SessionInfoKey);

        public static IConnectionSessionInfo GetSessionInfo(this IChannel channel) 
        {
            return channel.GetAttribute(SESSION_INFO).Get();
        }
    }
}
