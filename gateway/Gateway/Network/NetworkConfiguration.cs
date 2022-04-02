using System;
using System.Collections.Generic;
using System.Text;

namespace Gateway.Network
{
    public class NetworkConfiguration
    {
        public NetworkConfiguration()
        {
            SoBackLog = 1024 * 8;
            SendWindowSize = 128 * 1024;
            RecvWindowSize = 128 * 1024;
            ReadTimeout = 15;
            WriteTimeout = 15;
            WriteBufferHighWaterMark = 256 * 1024;
            WriteBufferLowWaterMark = 128 * 1024;
            ConnectTimeout = 5;
            EventLoopCount = 3;
        }

        public int SoBackLog { get; set; }
        public int SendWindowSize { get; set; }
        public int RecvWindowSize { get; set; }
        public int ReadTimeout { get; set; }
        public int WriteTimeout { get; set; }
        public int WriteBufferHighWaterMark { get; set; }
        public int WriteBufferLowWaterMark { get; set; }
        public int ConnectTimeout { get; set; }
        public int EventLoopCount { get; set; }
    }
}
