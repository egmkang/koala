using System;
using System.Buffers;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.Diagnostics.Contracts;
using System.Linq;
using System.Threading.Tasks;

namespace Gateway.Utils
{
    public unsafe struct MemoryWriter
    {
        private Memory<byte> buffer;
        private int pos;
        private readonly int maxSize;
        public MemoryWriter(Memory<byte> buffer, int size) 
        {
            this.buffer = buffer;
            this.pos = 0;
            this.maxSize = size;
        }

        private Span<byte> GetSpan(int size) 
        {
            var span = this.buffer.Span.Slice(pos, size);
            this.pos += size;
            Contract.Assert(this.pos <= this.maxSize);
            return span;
        }

        public void WriteInt8(byte v) 
        {
            var span = this.GetSpan(sizeof(byte));
            span[0] = v;
        }
        public void WriteInt16(short v) 
        {
            var span = this.GetSpan(sizeof(short));
            BinaryPrimitives.WriteInt16LittleEndian(span, v);
        }
        public void WriteInt32(int v) 
        {
            var span = this.GetSpan(sizeof(int));
            BinaryPrimitives.WriteInt32LittleEndian(span, v);
        }
        public void WriteInt64(long v) 
        {
            var span = this.GetSpan(sizeof(long));
            BinaryPrimitives.WriteInt64LittleEndian(span, v);
        }
        public void WriteBytes(byte[] v) 
        {
            this.WriteBytes(v, 0, v.Length);
        }
        public void WriteBytes(byte[] v, int offset, int length) 
        {
            var span = this.GetSpan(length);
            var vSpan = v.AsSpan();
            vSpan.Slice(offset, length).CopyTo(span);
        }
    }
}
