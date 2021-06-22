using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Connections;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Gateway
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env, IServiceProvider serviceProvider)
        {
            var clientFactory = serviceProvider.GetRequiredService<IConnectionFactory>();
            var connListnerFactory = serviceProvider.GetRequiredService<IConnectionListenerFactory>();
            app.UseWebSockets(new WebSocketOptions()
            {
                KeepAliveInterval = TimeSpan.FromSeconds(15),
            });

            app.Use(async (context, next) =>
            {
                if (context.Request.Path == "/ws")
                {
                    using (var ws = await context.WebSockets.AcceptWebSocketAsync())
                    {
                        var buffer = new byte[1024 * 4];
                        while (true)
                        {
                            var msg = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);
                            if (msg.CloseStatus.HasValue)
                            {
                                await ws.CloseAsync(msg.CloseStatus.Value, msg.CloseStatusDescription, CancellationToken.None);
                                break;
                            }
                            await ws.SendAsync(new ArraySegment<byte>(buffer, 0, msg.Count), msg.MessageType, msg.EndOfMessage, CancellationToken.None);
                        }
                        await Task.Delay(1000000000);
                    }
                }
                await next();
            });
        }
    }
}
