using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway.Message
{
    public struct RpcMessage
    {
        private static readonly byte[] Empty = new byte[0];

        public RpcMessage(RpcMeta meta, byte[] body) 
        {
            this.Meta = meta;
            this.Body = body != null ? body : Empty;
        }

        public RpcMeta Meta { get; private set; }
        public byte[] Body { get; private set; }
    }
}
