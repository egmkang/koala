using System;
using System.Buffers;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.Diagnostics.Contracts;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading.Tasks;

namespace Gateway.Utils
{
    public struct MemoryReader
    {
        private readonly ReadOnlySequence<byte> input;
        private int pos;
        private readonly int maxLength;

        public MemoryReader(ReadOnlySequence<byte> input)
        {
            this.input = input;
            this.pos = 0;
            this.maxLength = (int)input.Length;
        }

        public byte ReadInt8()
        {
            Span<byte> bytes = stackalloc byte[sizeof(long)];
            CopyTo<byte>(bytes);
            return bytes[0];
        }

        private void CopyTo<T>(Span<byte> bytes) where T : struct
        {
            var length = Marshal.SizeOf(default(T));
            this.input.Slice(this.pos, length).CopyTo(bytes);
            this.pos += length;
            Contract.Assert(this.pos <= maxLength);
        }

        private void CopyTo(Span<byte> bytes, int length) 
        {
            this.input.Slice(this.pos, length).CopyTo(bytes);
            this.pos += length;
            Contract.Assert(this.pos <= maxLength);
        }

        public short ReadInt16() 
        {
            Span<byte> bytes = stackalloc byte[sizeof(long)];
            CopyTo<short>(bytes);
            return BinaryPrimitives.ReadInt16LittleEndian(bytes);
        }
        public int ReadInt32() 
        {
            Span<byte> bytes = stackalloc byte[sizeof(long)];
            CopyTo<int>(bytes);
            return BinaryPrimitives.ReadInt32LittleEndian(bytes);
        }
        public long ReadInt64() 
        {
            Span<byte> bytes = stackalloc byte[sizeof(long)];
            CopyTo<long>(bytes);
            return BinaryPrimitives.ReadInt64LittleEndian(bytes);
        }
        public void ReadBytes(Span<byte> span, int length) 
        {
            CopyTo(span, length);
        }
    }
}
