using System;
using System.Collections.Generic;
using System.Text;

namespace Gateway.Utils
{
    public class TimeBasedSequence : UniqueSequence
    {
        public void SetTime(long time) 
        {
            this.SetHighPart(time);
        }
    }
}
