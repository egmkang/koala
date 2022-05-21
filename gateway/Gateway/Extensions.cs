using System;
using System.Collections.Generic;
using System.Text;
using System.Security.Cryptography;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Gateway.Extersions;
using Microsoft.Extensions.DependencyInjection;
using Gateway.Handler;
using System.Threading.Tasks;
using Microsoft.Extensions.Options;
using Microsoft.Extensions.Logging;
using Abstractions.Placement;
using Gateway.Utils;
using Gateway.Message;
using Gateway.Gateway;

namespace Gateway
{
    public static partial class Extensions
    {
        public static async Task RunGatewayAsync(this ServiceBuilder builder)
        {
            var config = builder.ServiceProvider.GetRequiredService<IOptionsMonitor<GatewayConfiguration>>().CurrentValue;
            var logger = builder.ServiceProvider.GetRequiredService<ILoggerFactory>().CreateLogger("F1.Gateway");

            logger.LogInformation("RunGatewayAsync, PlacementDriverAddress:{0}, Host ListenPort:{1}, GatewayAddress:{2}",
                                    config.PlacementDriverAddress, config.ListenPort, config.GatewayAddress);
            builder.SetPDAddress(config.PlacementDriverAddress);
            var handlerFactory = new MessageHandlerFactory(builder.ServiceProvider);
            var gatewayClientFactory = builder.ServiceProvider.GetRequiredService<GatewayClientFactory>();
            await builder.Listen(config.ListenPort, handlerFactory, new RpcMessageCodec()).ConfigureAwait(false);
            await builder.PrepareGatewayAndRunAsync(config, logger);
        }

        private static async Task PrepareGatewayAndRunAsync(this ServiceBuilder builder, 
                                                            GatewayConfiguration config,
                                                            ILogger logger)
        {
            var provider = builder.ServiceProvider;
            var placement = provider.GetRequiredService<IPlacement>();
            var sessionUniqueSequence = provider.GetRequiredService<SessionUniqueSequence>();

            var messageHandler = provider.GetRequiredService<GatewayMessageHandler>();
            messageHandler.PrivateKey = config.PrivateKey;
            messageHandler.DisableTokenCheck = config.DisableTokenCheck;
            messageHandler.AuthService = config.AuthService;

            var port = config.GetGatewayWebSocketPort();
            var websocketPath = config.GetGatewayWebSocketPath();
            await builder.ListenWebSocket(port, websocketPath, 
                                            new WebSocketMessageHandlerFactory(builder.ServiceProvider), 
                                            new BlockMessageCodec()).ConfigureAwait(false);

            try
            {
                var ServerID = await placement.GenerateServerIDAsync();
                sessionUniqueSequence.SetServerID(ServerID);

                logger.LogInformation("GetServerID, ServerID:{0}, Address:{1}", ServerID, config.ListenAddress);

                var LeaseID = await placement.RegisterServerAsync(new PlacementActorHostInfo()
                {
                    ServerID = ServerID,
                    Address = config.ListenAddress,
                    StartTime = Platform.GetMilliSeconds(),
                    TTL = config.KeepAliveInterval * 3,
                    Desc = $"Gateway_{ServerID}",
                    Services = new Dictionary<string, string>() { { "IGateway", "GatewayImpl" } },
                    Labels = new Dictionary<string, string>() { { "GatewayAddress", config.GatewayAddress } },
                });
                logger.LogInformation("RegisterServer Success, LeaseID:{0}", LeaseID);
            }
            catch (Exception e)
            {
                logger.LogError("StartUp Gateway, Exception:{0}", e);
            }

            _ = placement.StartPullingAsync().ContinueWith((t) =>
            {
                logger.LogError("PDKeepAlive Process Exit");
                NLog.LogManager.Flush();
                Environment.Exit(-1);
            });
        }

        public static void AddGatewayServices(this ServiceBuilder builder)
        {
            var services = builder.ServiceCollection;

            services.AddSingleton<GatewayMessageHandler>();
        }

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
            ArgumentNullException.ThrowIfNull(firstPacket);
            var dict = new Dictionary<string, string>();
            foreach (var (k, v) in firstPacket) 
            {
                dict[k.ToString()] = v?.ToString();
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
    }
}
