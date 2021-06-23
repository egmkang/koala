﻿using System;
using System.Buffers;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Gateway.Utils;

namespace Gateway.Message
{
    /// <summary>
    /// 4字节magic `KOLA`
    /// 4字节小端Meta Length
    /// 4字节小端Body Length
    /// N字节Meta
    /// M字节Body
    /// </summary>
    public unsafe class RpcMessageCodec
    {
        readonly int Magic = MakeMagic("KOLA");
        const int HeaderLength = sizeof(int) + sizeof(int) + sizeof(int);
        static Dictionary<string, Type> MessageTypes = new Dictionary<string, Type>();
        readonly byte[] Empty = new byte[0];
        static RpcMessageCodec()
        {
            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (var asm in assemblies.Reverse()) 
            {
                foreach (var t in asm.GetTypes())
                {
                    if (t.IsSubclassOf(typeof(RpcMeta))) 
                    {
                        MessageTypes.Add(t.Name, t);
                    }
                }
            }
        }
        public (Memory<byte> memory, int size) Encode(IBufferWriter<byte> writer, RpcMessage msg)
        {
            var name = StringMap.GetStringBytes(msg.Meta.GetType().Name);
            var meta = JsonSerializer.SerializeToUtf8Bytes(msg.Meta as object);
            var metaLength = 1 + name.Length + meta.Length;
            var bodyLength = msg.Body != null ? msg.Body.Length : 0;
            var totalLength = HeaderLength + metaLength + bodyLength;

            var memory = writer.GetMemory(totalLength);
            var memoryWrite = new MemoryWriter(memory, totalLength);
            memoryWrite.WriteInt32(Magic);
            memoryWrite.WriteInt32(metaLength);
            memoryWrite.WriteInt32(bodyLength);

            // 1字节NameLength + Name + M字节Meta
            memoryWrite.WriteInt8((byte)name.Length);
            memoryWrite.WriteBytes(name);
            memoryWrite.WriteBytes(meta);

            if (msg.Body != null && msg.Body.Length > 0) 
            {
                memoryWrite.WriteBytes(msg.Body);
            }

            return (memory, totalLength);
        }

        public int Decode(ReadOnlySequence<byte> input, out RpcMessage msg) 
        {
            msg = default;
            if (input.Length < HeaderLength) 
            {
                return 0;
            }

            var memoryReader = new MemoryReader(input);

            var magic = memoryReader.ReadInt32();
            var metaLength = memoryReader.ReadInt32();
            var bodyLength = memoryReader.ReadInt32();
            var totalLength = HeaderLength + metaLength + bodyLength;
            if (input.Length < totalLength) 
            {
                return 0;
            }
            var nameLength = memoryReader.ReadInt8();
            Span<byte> messageName = stackalloc byte[nameLength];
            memoryReader.ReadBytes(messageName, nameLength);
            var name = Encoding.UTF8.GetString(messageName);
            if (!MessageTypes.TryGetValue(name, out var messageType)) 
            {
                throw new Exception($"Message:{name} not found");
            }

            var metaBodyLength = metaLength - 1 - name.Length;
            byte[] metaBody = ArrayPool<byte>.Shared.Rent(metaBodyLength);
            try 
            {
                memoryReader.ReadBytes(metaBody.AsSpan(), metaBodyLength);
                var meta = JsonSerializer.Deserialize(new ReadOnlySpan<byte>(metaBody, 0, metaBodyLength), messageType);
                var body = Empty;
                if (bodyLength > 0) 
                {
                    body = new byte[bodyLength];
                    memoryReader.ReadBytes(body.AsSpan(), bodyLength);
                }
                msg = new RpcMessage(meta as RpcMeta, body);
                return totalLength;
            }
            finally 
            {
                ArrayPool<byte>.Shared.Return(metaBody);
            }
        }

        private static int MakeMagic(string magic) 
        {
            var bytes = Encoding.UTF8.GetBytes(magic);
            fixed (byte* p = bytes) 
            {
                return *(int*)p;
            }
        }
    }

    public class ClientMessageCodec 
    {
    }
}
