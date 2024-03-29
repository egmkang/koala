﻿using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.Extensions.DependencyInjection;
using Abstractions;
using Abstractions.Placement;
using Abstractions.Network;
using Gateway.Message;
using Gateway.Network;

namespace Gateway.Extersions
{
    public class ServiceBuilder : IServiceBuilder
    {
        private readonly ServiceCollection serviceCollection = new ServiceCollection();
        private IServiceProvider? provider;
        public IServiceProvider ServiceProvider
        {
            get
            {
                ArgumentNullException.ThrowIfNull(this.provider);
                return this.provider;
            }
        }
        public IServiceCollection ServiceCollection => this.serviceCollection;

        public bool Running { get; set; } = true;

        private int shutingDown = 0;

        public IServiceBuilder Build()
        {
            this.provider = serviceCollection.BuildServiceProvider();
            return this;
        }

        public void SetPDAddress(string pdAddress) 
        {
            var placement = this.ServiceProvider.GetRequiredService<IPlacement>();
            placement.SetPlacementServerInfo(pdAddress);
        }

        public async Task Listen(int port, IMessageHandlerFactory factory, IMessageCodec codec) 
        {
            var connectionListener = this.ServiceProvider.GetRequiredService<IConnectionListener>();
            var messageCenter = this.ServiceProvider.GetRequiredService<IMessageCenter>();
            var clientFactory = this.ServiceProvider.GetRequiredService<IClientConnectionFactory>();
            var clientConnectionPool = this.ServiceProvider.GetRequiredService<ClientConnectionPool>();
            factory.Codec = codec;

            clientFactory.Init();

            connectionListener.Init();
            await connectionListener.BindAsync(port, factory).ConfigureAwait(false);
            clientConnectionPool.MessageHandlerFactory = factory;
        }

        public async Task ListenWebSocket(int port, string websocketPath, IMessageHandlerFactory factory, IMessageCodec codec) 
        {
            var connectionListener = this.ServiceProvider.GetRequiredService<IConnectionListener>();
            var messageCenter = this.ServiceProvider.GetRequiredService<IMessageCenter>();
            var clientFactory = this.ServiceProvider.GetRequiredService<IClientConnectionFactory>();
            factory.Codec = codec;

            clientFactory.Init();

            connectionListener.Init();
            await connectionListener.BindWebSocketAsync(port, websocketPath, factory).ConfigureAwait(false);
        }

        public void ShutDown()
        {
            this.Running = false;

            if (Interlocked.Increment(ref this.shutingDown) == 1) 
            {
                var listener = this.ServiceProvider.GetRequiredService<IConnectionListener>();
                listener.ShutdDownAsync().Wait();
                var connectionFactory = this.ServiceProvider.GetRequiredService<IClientConnectionFactory>();
                connectionFactory.ShutdDownAsync().Wait();
            }
        }
    }
}
