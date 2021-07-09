using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Text;
using System.Security.Cryptography;
using Gateway.Handler;
using Gateway.Network;
using Gateway.Placement;
using Gateway.Utils;
using Microsoft.AspNetCore.Connections;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using NLog.Extensions.Logging;

namespace Gateway
{
    public static partial class Extensions
    {
        public static unsafe int CastToInt(this string str)
        {
            var bytes = Encoding.UTF8.GetBytes(str);
            fixed (byte* p = bytes)
            {
                return *(int*)p;
            }
        }

        public static Dictionary<string, string> DecodeFirstMessage(this Memory<byte> memory, int size) 
        {
            ReadOnlySpan<byte> span = memory.Span.Slice(0, size);
            return span.DecodeFirstMessage();
        }

        public static Dictionary<string, string> DecodeFirstMessage(this ReadOnlySpan<byte> memory)
        {
            var firstPacket = JsonConvert.DeserializeObject(Encoding.UTF8.GetString(memory)) as JObject;
            var dict = new Dictionary<string, string>();
            foreach (var (k, v) in firstPacket) 
            {
                dict[k.ToString()] = v.ToString();
            }
            return dict;
        }

        public static bool ComputeHash(this Dictionary<string, string> firstMessage, string privateKey, string checkSumKey = "check_sum") 
        {
            var sb = new StringBuilder(1024);
            var inputCheckSum = "";
            var list = new List<(string, string)>(firstMessage.Count);


            foreach (var k in firstMessage.Keys) 
            {
                if (k as string == checkSumKey) 
                {
                    inputCheckSum = firstMessage[k].ToString();
                    continue;
                }
                list.Add((k, firstMessage[k]));
            }

            list.Sort((x1, x2) => x1.Item1.CompareTo(x2.Item1));

            foreach (var (k, v) in list) 
            {
                sb.Append(k);
                sb.Append(v);
            }

            sb.Append(privateKey);

            var checkSum = "";
            var input = Encoding.UTF8.GetBytes(sb.ToString());
            using (SHA256 sha256Hash = SHA256.Create()) 
            {
                byte[] data = sha256Hash.ComputeHash(input);

                var sBuilder = new StringBuilder();

                for (int i = 0; i < data.Length; i++)
                {
                    sBuilder.Append(data[i].ToString("x2"));
                }

                checkSum = sBuilder.ToString();
            }

            return checkSum == inputCheckSum;
        } 

        public static void ConfigureServices(this IServiceCollection services)
        {
            Type connectionFactoryType = GetSocketConnectionFactory();
            if (connectionFactoryType == null)
            {
                throw new Exception("SocketConnectionFactory Not Found");
            }

            services.AddLogging(builder =>
            {
                builder.ClearProviders();
                builder.SetMinimumLevel(LogLevel.Debug);
                builder.AddNLog();
            });

            services.AddSingleton<IMessageCenter, MessageCenter>();
            services.AddSingleton(typeof(IConnectionFactory), connectionFactoryType);
            services.AddSingleton<IPlacement, PDPlacement>();
            services.AddSingleton<SessionUniqueSequence>();
            services.AddSingleton<SessionManager>();
            services.AddSingleton<ClientConnectionPool>();
            services.AddSingleton<MessageHandler>();
        }

        static Type GetSocketConnectionFactory() 
        {
            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (var asm in assemblies)
            {
                var type = asm.GetType("Microsoft.AspNetCore.Server.Kestrel.Transport.Sockets.SocketConnectionFactory");
                if (type != null) return type;
            }
            return null;
        }
    }
}
