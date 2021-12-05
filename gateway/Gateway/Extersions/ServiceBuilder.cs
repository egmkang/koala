using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using System.Threading;
using Microsoft.Extensions.DependencyInjection;
using Abstractions;
using Abstractions.Placement;
using Abstractions.Network;
using Gateway.Message;

namespace Gateway.Extersions
{
    public class ServiceBuilder : IServiceBuilder
    {
        private readonly ServiceCollection serviceCollection = new ServiceCollection();
        private IServiceProvider serviceProvider;
        public IServiceProvider ServiceProvider => this.serviceProvider;
        public IServiceCollection ServiceCollection => this.serviceCollection;

        public bool Running { get; set; } = true;

        private int shutingDown = 0;

        public IServiceBuilder Build()
        {
            this.serviceProvider = serviceCollection.BuildServiceProvider();
            return this;
        }

        public async Task InitAsync(string pdAddress, int port) 
        {
            var placement = this.serviceProvider.GetRequiredService<IPlacement>();
            placement.SetPlacementServerInfo(pdAddress);

            await this.Listen(port).ConfigureAwait(false);
        }

        private async Task Listen(int port) 
        {
            var connectionListener = this.ServiceProvider.GetRequiredService<IConnectionListener>();
            var messageCenter = this.ServiceProvider.GetRequiredService<IMessageCenter>();
            var messageHandlerFactory = this.ServiceProvider.GetRequiredService<IMessageHandlerFactory>();
            var clientFactory = this.ServiceProvider.GetRequiredService<IClientConnectionFactory>();
            messageHandlerFactory.Codec = new RpcMessageCodec();

            clientFactory.Init();

            connectionListener.Init();
            await connectionListener.BindAsync(port, messageHandlerFactory).ConfigureAwait(false);
        }

        public void ShutDown()
        {
            this.Running = false;

            if (Interlocked.Increment(ref this.shutingDown) == 1) 
            {
                var listener = this.serviceProvider.GetRequiredService<IConnectionListener>();
                listener.ShutdDownAsync().Wait();
                var connectionFactory = this.serviceProvider.GetRequiredService<IClientConnectionFactory>();
                connectionFactory.ShutdDownAsync().Wait();
            }
        }
    }
}
