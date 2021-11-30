using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;

namespace Gateway.Utils
{
    public class AtomicInt64
    {
        public AtomicInt64()
        {
            value = 0L;
        }

        public AtomicInt64(Int64 v)
        {
            value = v;
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static implicit operator Int64(AtomicInt64 v)
        {
            return v.Load();
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public Int64 Load()
        {
            return Interlocked.Read(ref value);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public void Store(Int64 v)
        {
            this.value = v;
            Interlocked.MemoryBarrier();
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public Int64 GetAndInc()
        {
            return this.Add(1);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public bool CompareExchange(Int64 old_value, Int64 new_value)
        {
            return old_value == Interlocked.CompareExchange(ref this.value, new_value, old_value);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static AtomicInt64 operator ++(AtomicInt64 value)
        {
            return new AtomicInt64(value.Inc());
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static AtomicInt64 operator --(AtomicInt64 value)
        {
            return new AtomicInt64(value.Dec());
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public Int64 Dec() 
        {
            return Interlocked.Decrement(ref this.value);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public Int64 Inc() 
        {
            return Interlocked.Increment(ref this.value);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public Int64 Add(Int32 v)
        {
            return Interlocked.Add(ref this.value, (Int64)v);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public Int64 Add(Int64 v)
        {
            return Interlocked.Add(ref this.value, v);
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static AtomicInt64 operator +(AtomicInt64 a, AtomicInt64 b)
        {
            return new AtomicInt64(a.Load() + b.Load());
        }

        private Int64 value = 0L;
        private readonly Int64 _1, _2, _3, _4, _5;
    }

}
