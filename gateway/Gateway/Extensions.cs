using System;
using System.Collections.Generic;
using System.Text;
using Gateway.Handler;
using Gateway.Network;
using Gateway.Placement;
using Gateway.Utils;
using Microsoft.AspNetCore.Connections;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using NLog.Extensions.Logging;

namespace Gateway
{
    public static partial class Extensions
    {
        public static unsafe int CastToInt(this string str) 
        {
            var bytes = Encoding.UTF8.GetBytes(str);
            fixed (byte* p = bytes) 
            {
                return *(int*)p;
            }
        }

        public static void ConfigureServices(this IServiceCollection services)
        {
            Type connectionFactoryType = GetSocketConnectionFactory();
            if (connectionFactoryType == null)
            {
                throw new Exception("SocketConnectionFactory Not Found");
            }

            services.AddLogging(builder =>
            {
                builder.ClearProviders();
                builder.SetMinimumLevel(LogLevel.Debug);
                builder.AddNLog();
            });

            services.AddSingleton<IMessageCenter, MessageCenter>();
            services.AddSingleton(typeof(IConnectionFactory), connectionFactoryType);
            services.AddSingleton<IPlacement, PDPlacement>();
            services.AddSingleton<SessionUniqueSequence>();
            services.AddSingleton<SessionManager>();
            services.AddSingleton<ClientConnectionPool>();
            services.AddSingleton<MessageHandler>();
        }

        static Type GetSocketConnectionFactory() 
        {
            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (var asm in assemblies)
            {
                var type = asm.GetType("Microsoft.AspNetCore.Server.Kestrel.Transport.Sockets.SocketConnectionFactory");
                if (type != null) return type;
            }
            return null;
        }
    }
}
