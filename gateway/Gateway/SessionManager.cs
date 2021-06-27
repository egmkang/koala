using System;
using System.Collections.Concurrent;
using System.Linq;
using System.Net.WebSockets;
using System.Threading.Tasks;
using Gateway.Utils;
using Microsoft.Extensions.Logging;

namespace Gateway
{
    public class SessionManager
    {
        private readonly ILogger logger;
        private readonly SessionUniqueSequence sessionSequence;
        private readonly ConcurrentDictionary<long, ISession> sessions = new ConcurrentDictionary<long, ISession>(4, 10 * 1024);

        public SessionManager(ILogger logger, SessionUniqueSequence sessionSequence) 
        {
            this.logger = logger;
            this.sessionSequence = sessionSequence;
        }

        public long NewSessionID => sessionSequence.NewSessionID;

        public ISession GetSession(long sessionID) 
        {
            if (this.sessions.TryGetValue(sessionID, out var session))
            {
                return session;
            }
            return null;
        }

        public void AddSession(ISession session) 
        {
            sessions.TryAdd(session.SessionID, session);
            logger.LogInformation("SessionManager.AddSession, SessionID:{0}, SessionType:{1}", session.SessionID, session.SessionType);
        }

        public void RemoveSession(long sessionID) 
        {
            if (sessions.TryRemove(sessionID, out var session) && session != null) 
            {
                logger.LogInformation("SessionManager.RemoveSession, SessionID:{0}, SessionType:{1}", session.SessionID, session.SessionType);
            }
        }
    }
}
