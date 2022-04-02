using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Microsoft.Extensions.Logging;
using NLog.Extensions.Logging;
using Abstractions;
using Gateway.Utils;
using Abstractions.Network;
using Gateway.Network;
using Gateway.Message;
using Gateway.Gateway;
using Abstractions.Placement;
using Gateway.Placement;
using Microsoft.Extensions.Configuration;

namespace Gateway.Extersions
{
    public static class Extensions
    {
        public static void AddDefaultServices(this IServiceBuilder builder)
        {
            AssemblyLoader.LoadAssemblies();

            var services = builder.ServiceCollection;

            services.AddOptions();
            services.AddLogging();

            services.TryAddSingleton<IConnectionManager, ConnectionManager>();
            services.TryAddSingleton<IConnectionSessionInfoFactory, DefaultConnectionSessionInfoFactory>();
            services.TryAddSingleton<IClientConnectionFactory, ClientConnectionFactory>();
            services.TryAddSingleton<IConnectionListener, ConnectionListener>();
            services.TryAddSingleton<IMessageCenter, MessageCenter>();
            services.TryAddSingleton<IPlacement, PDPlacement>();
            services.TryAddSingleton<TimeBasedSequence>();
            services.TryAddSingleton<SessionUniqueSequence>();
            services.TryAddSingleton<ClientConnectionPool>();
            services.TryAddSingleton<GatewayClientFactory>();
            services.TryAddSingleton<SendingThreads>();
        }

        public static void AddLog(this IServiceBuilder serviceBuilder, IConfiguration config) 
        {
            var services = serviceBuilder.ServiceCollection;

            services.AddLogging(builder =>
            {
                builder.ClearProviders();
                builder.AddConfiguration(config.GetSection("Logging"));
                builder.AddNLog();
            });
        }

        public static ServiceBuilder Configure<T>(this ServiceBuilder builder, Action<T> action) where T : class
        {
            builder.ServiceCollection.Configure<T>(action);
            return builder;
        }
    }
}
