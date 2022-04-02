using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.Extensions.DependencyInjection;

namespace Abstractions
{
    public interface IServiceBuilder
    {
        IServiceProvider ServiceProvider { get; }
        IServiceCollection ServiceCollection { get; }

        IServiceBuilder Build();

        bool Running { get; }

        void ShutDown();
    }
}
