using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using Microsoft.Extensions.Logging;
using Gateway.Utils;
using Abstractions.Network;

namespace Gateway.NetworkNetty
{
    public sealed class DefaultConnectionSessionInfoFactory : IConnectionSessionInfoFactory
    {
        private readonly ILogger logger;
        private readonly SendingThreads sendingThreads;
        private readonly SessionUniqueSequence sessionUniqueSequence;

        public DefaultConnectionSessionInfoFactory(ILoggerFactory loggerFactory, 
                                                    SendingThreads sendingThreads,
                                                    SessionUniqueSequence sessionUniqueSequence) 
        {
            this.logger = loggerFactory.CreateLogger("SessionInfo");
            this.sendingThreads = sendingThreads;
            this.sessionUniqueSequence = sessionUniqueSequence;

            logger.LogInformation("DefaultChannelSessionInfo, SessionIDSeed:{0}", this.sessionUniqueSequence.GetNewSequence());
        }

        public IConnectionSessionInfo NewSessionInfo(IMessageHandlerFactory handlerFactory)
        {
            return new DefaultConnectionSessionInfo(this.sessionUniqueSequence.GetNewSequence(),
                                                    this.logger, handlerFactory.Codec, this.sendingThreads);
        }
    }
}
