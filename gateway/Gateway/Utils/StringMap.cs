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
        private static Dictionary<string, byte[]> cache = new Dictionary<string, byte[]>();

        public static byte[] GetStringBytes(string str)
        {
            if (cache.TryGetValue(str, out var bytes))
            {
                return bytes;
            }

            bytes = Encoding.UTF8.GetBytes(str);

            lock (mutex)
            {
                var table = new Dictionary<string, byte[]>(cache);
                table.TryAdd(str, bytes);
                cache = table;
            }

            return bytes;
        }
    }
}
