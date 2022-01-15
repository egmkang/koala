using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Gateway.Utils
{
    public static class StringMap
    {
        private static readonly object mutex = new object();
        private static Dictionary<object, byte[]> cache = new Dictionary<object, byte[]>();

        public static byte[] GetCachedStringBytes(object o, Func<object, string> fn)
        {
            if (cache.TryGetValue(o, out var bytes))
            {
                return bytes;
            }

            bytes = Encoding.UTF8.GetBytes(fn(o));

            lock (mutex)
            {
                var table = new Dictionary<object, byte[]>(cache);
                table.TryAdd(o, bytes);
                cache = table;
            }

            return bytes;
        }
    }
}
