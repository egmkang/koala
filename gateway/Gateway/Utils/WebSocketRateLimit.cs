using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway.Utils
{
    public class WebSocketRateLimit
    {
        private int count = 0;
        private long lastTime = Platform.GetSeconds();
        private const int UnLimited = 10000;

        public int GetCurrentCount() 
        {
            var time = Platform.GetSeconds();
            if (time != lastTime) 
            {
                var delta = (int)(lastTime - time) * (Limit == 0 ? UnLimited : Limit);
                this.count = this.count - delta > 0 ? this.count - delta : 0;
            }
            return this.count;
        }

        public int Inc() 
        {
            var _ = this.GetCurrentCount();
            return ++this.count;
        }

        public static int Limit { get; set; } = 10;
    }
}
