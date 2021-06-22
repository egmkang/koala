using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway.Message
{
    public class RpcMessage
    {
        public RpcMeta Meta { get; set; }
        public byte[] Body { get; set; }
    }
}
