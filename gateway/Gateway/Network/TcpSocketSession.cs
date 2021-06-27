using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Gateway.Message;
using Gateway.Utils;
using Microsoft.AspNetCore.Connections;

namespace Gateway.Network
{
    public class TcpSocketSession : ISession
    {
        private readonly long sessionID;
        private readonly ConnectionContext connection;
        private readonly ISessionInfo sessionInfo;
        private readonly CancellationTokenSource cancellationTokenSource = new CancellationTokenSource();
        private readonly RpcMessageCodec codec = new RpcMessageCodec();

        public TcpSocketSession(long sessionID, ConnectionContext connection, ISessionInfo sessionInfo) 
        {
            this.sessionID = sessionID;
            this.connection = connection;
            this.sessionInfo = sessionInfo;
            this.RemoteAddress = this.connection.RemoteEndPoint.ToString();
            this.LastMessageTime = Platform.GetMilliSeconds();
        }

        public long SessionID => this.sessionID;

        public string RemoteAddress { get; private set; }

        public SessionType SessionType => SessionType.SessionType_Socket;

        public long LastMessageTime { get; set; }

        public ISessionInfo UserData => this.sessionInfo;

        public bool IsActive => !this.cancellationTokenSource.IsCancellationRequested;

        public Task CloseAsync()
        {
            throw new NotImplementedException();
        }

        private Task SendLoop() 
        {
            return Task.CompletedTask;
        }

        public Task RecvLoop()
        {
            throw new NotImplementedException();
        }

        public Task SendMessage(object msg)
        {
            throw new NotImplementedException();
        }
    }
}
