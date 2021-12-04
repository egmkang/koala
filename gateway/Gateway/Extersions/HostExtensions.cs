using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace Gateway.Extersions
{
    public static class HostExtensions
    {
        public static async Task RunHostAsync(this ServiceBuilder builder) 
        {
            var config = builder.ServiceProvider.GetRequiredService<IOptionsMonitor<GatewayConfiguration>>().CurrentValue;
            var logger = builder.ServiceProvider.GetRequiredService<ILoggerFactory>().CreateLogger("Network");

            logger.LogInformation("RunHostAsync, PlacementDriverAddress:{0}, Host ListenPort:{1}",
                                    config.PlacementDriverAddress, config.ListenPort);

            await builder.InitAsync(config.PlacementDriverAddress, config.ListenPort).ConfigureAwait(false);
        }
    }
}
