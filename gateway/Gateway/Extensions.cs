using System;
using System.Collections.Generic;
using System.Diagnostics.Contracts;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Gateway.Network;
using Gateway.Placement;
using Gateway.Utils;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Connections;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

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

        public static void ListenSocket(this IServiceProvider serviceProvider, int port) 
        {
        }

        public static void ListenWebSocket(this IApplicationBuilder app, 
                                            IServiceProvider serviceProvider, 
                                            string path) 
        {
            var manager = serviceProvider.GetRequiredService<SessionManager>();
            var loggerFactory = serviceProvider.GetRequiredService<ILoggerFactory>();
            var messageCenter = serviceProvider.GetRequiredService<IMessageCenter>();
            var logger = loggerFactory.CreateLogger("WebSocket");

            app.UseForwardedHeaders(new ForwardedHeadersOptions
            {
                ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto,
            });

            app.UseWebSockets(new WebSocketOptions()
            {
                KeepAliveInterval = TimeSpan.FromSeconds(15),
            });

            app.Use(async (context, next) =>
            {
                if (context.Request.Path == path)
                {
                    var address = context.Connection.RemoteIpAddress.ToString();
                    using (var websocket = await context.WebSockets.AcceptWebSocketAsync())
                    {
                        var sessionInfo = new DefaultSessionInfo(manager.NewSessionID, 0);
                        try
                        {
                            var session = new WebSocketSession(sessionInfo.SessionID, websocket, address, logger, messageCenter, sessionInfo);
                            manager.AddSession(session);
                            await session.RecvLoop().ConfigureAwait(false);
                        }
                        catch (Exception e) 
                        {
                            logger.LogError("WebSocket, SessionID:{0}, Address:{1}, Exception:{2}",
                                sessionInfo.SessionID, address, e);
                        }
                    }
                }
                await next();
            });
        } 

        public static void ConfigureServices(this IServiceCollection services)
        {
            Type connectionFactoryType = GetSocketConnectionFactory();
            if (connectionFactoryType == null)
            {
                throw new Exception("SocketConnectionFactory Not Found");
            }
            services.AddSingleton<IMessageCenter, MessageCenter>();
            services.AddSingleton(typeof(IConnectionFactory), connectionFactoryType);
            services.AddSingleton<IPlacement, PDPlacement>();
            services.AddSingleton<SessionUniqueSequence>();
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
