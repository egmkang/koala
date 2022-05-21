using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text;

namespace Gateway.Utils
{
    public class LRU<K, V> where V : class
                           where K: notnull
    {
        private readonly object mutex = new object();
        private readonly LinkedList<ValueTuple<K, V>> list = new LinkedList<ValueTuple<K, V>>();
        private readonly Dictionary<K, LinkedListNode<ValueTuple<K, V>>> dict = new Dictionary<K, LinkedListNode<ValueTuple<K, V>>>();
        private readonly int capacity;

        public LRU(int size)
        {
            capacity = size;
        }

        public bool TryAdd(K k, V v)
        {
            lock (mutex)
            {
                if (dict.TryGetValue(k, out var vv))
                {
                    return false;
                }
                list.AddLast((k, v));
                vv = list.Last;
                ArgumentNullException.ThrowIfNull(vv);
                dict.Add(k, vv);

                if (dict.Count > capacity)
                {
                    var delete = list.First;
                    if (delete == null) 
                    {
                        return true;
                    }
                    dict.Remove(delete.Value.Item1);
                    list.Remove(delete);
                }
                return true;
            }
        }

        public void Add(K k, V v)
        {
            lock (mutex)
            {
                if (dict.TryGetValue(k, out var vv))
                {
                    list.Remove(vv);
                    list.AddLast(vv);
                    vv.Value = (k, v);
                    return;
                }
                list.AddLast((k, v));
                vv = list.Last;
                ArgumentNullException.ThrowIfNull(vv);
                dict.Add(k, vv);

                if (dict.Count > capacity)
                {
                    var delete = list.First;
                    if (delete == null) 
                    {
                        return;
                    }
                    dict.Remove(delete.Value.Item1);
                    list.Remove(delete);
                }
            }
        }

        public bool Get(K k, [MaybeNullWhen(false)] out V value)
        {
            lock (mutex)
            {
                if (dict.TryGetValue(k, out var v))
                {
                    list.Remove(v);
                    list.AddLast(v);
                    value = v.Value.Item2;
                    return true;
                }
                value = default(V);
                return false;
            }
        }

        public void Remove(K k)
        {
            lock (mutex)
            {
                if (dict.Remove(k, out var v))
                {
                    list.Remove(v);
                }
            }
        }
    }
}