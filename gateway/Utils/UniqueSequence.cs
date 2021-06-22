using System;
using System.Collections.Generic;
using System.Diagnostics.Contracts;
using System.Text;
using System.Threading;

namespace Gateway.Utils
{
    public class UniqueSequence
    {
        public const long HighPartShift = 10_000_000_000;

        public long GetNewSequence()
        {
            return Interlocked.Increment(ref sequence);
        }

        public void SetHighPart(long h)
        {
            Contract.Assert(h * HighPartShift > Interlocked.Read(ref sequence));

            var highPart = h * HighPartShift;
            Interlocked.Add(ref sequence, highPart);
        }

        private long sequence;
    }

    public class SessionUniqueSequence : UniqueSequence
    {
        public static long GetServerID(long seq)
        {
            return seq / HighPartShift;
        }

        public void SetServerID(long serverID)
        {
            SetHighPart(serverID);
        }

        public long NewSessionID => GetNewSequence();
    }

}