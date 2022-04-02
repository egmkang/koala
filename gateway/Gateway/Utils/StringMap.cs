using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Gateway.Utils
{
    public static class StringMap
    {
        // TODO: generic Cache
        private static readonly object mutex = new object();
        private static Dictionary<object, byte[]> cache = new Dictionary<object, byte[]>();
        private static readonly object mutext2 = new object();
        private static Dictionary<object, string> stringCache = new Dictionary<object, string>();

        public static string GetCachedString(object o, Func<object, string> fn) 
        {
            if (stringCache.TryGetValue(o, out var str))
            {
                return str;
            }

            str = fn(o);

            lock (mutex)
            {
                var table = new Dictionary<object, string>(stringCache);
                table.TryAdd(o, str);
                stringCache = table;
            }

            return str;
        }

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
