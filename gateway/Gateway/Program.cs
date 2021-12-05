using System;
using System.Threading.Tasks;
using Gateway.Extersions;
using Microsoft.Extensions.Configuration;

namespace Gateway
{
    public class Program
    {
        public static async Task Main(string[] args)
        {
            var configuration = new ConfigurationBuilder()
                     .AddJsonFile("appsettings.json")
                     .Build();

            var builder = new ServiceBuilder();

            builder.Configure<GatewayConfiguration>((config) =>
            {
                configuration.GetSection("Gateway").Bind(config);
            });

            builder.AddDefaultServices();
            builder.AddGatewayServices();
            builder.AddLog();

            builder.Build();

            await builder.RunGatewayAsync();

            while (true)
            {
                await Task.Delay(1000).ConfigureAwait(false);
            }
        }
    }
}
