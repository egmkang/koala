using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Gateway.Placement;
using Gateway.Utils;
using Microsoft.AspNetCore.Connections;
using Microsoft.Extensions.DependencyInjection;

namespace Gateway
{
    public static class Extensions
    {
        public static void ConfigureServices(this IServiceCollection services)
        {
            Type connectionFactoryType = GetSocketConnectionFactory();
            if (connectionFactoryType == null)
            {
                throw new Exception("SocketConnectionFactory Not Found");
            }
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
