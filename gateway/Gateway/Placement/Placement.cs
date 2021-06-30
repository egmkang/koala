using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Gateway.Utils;
using Microsoft.Extensions.Logging;
using static Gateway.Placement.IPlacement;

namespace Gateway.Placement
{
    public static partial class Extensions
    {
        static readonly MediaTypeHeaderValue HeaderJson = new MediaTypeHeaderValue("application/json");
        public static HttpContent AsJson(this object o)
        {
            var content = new ByteArrayContent(JsonSerializer.SerializeToUtf8Bytes(o));
            content.Headers.ContentType = HeaderJson;
            return content;
        }
    }

    public sealed class PDPlacement : IPlacement
    {
        private readonly HttpClient httpClient = new HttpClient(new HttpClientHandler()
        {
            Proxy = null,
            UseProxy = false,
        });
        const int ServerLRUSize = 1024;
        private readonly ILogger logger;
        private readonly LRU<string, PlacementFindActorPositionResponse> positionLru = new LRU<string, PlacementFindActorPositionResponse>(10 * 10000);
        private readonly LRU<long, object> addedServer = new LRU<long, object>(ServerLRUSize);
        private readonly LRU<long, object> removedServer = new LRU<long, object>(ServerLRUSize);
        private readonly LRU<long, object> offlineServer = new LRU<long, object>(ServerLRUSize);
        private Dictionary<long, PlacementActorHostInfo> host = new Dictionary<long, PlacementActorHostInfo>(); //readonly
        private PlacementActorHostInfo currentServerInfo = new PlacementActorHostInfo();
        private OnAddServer onAddServer;
        private OnRemoveServer onRemoveServer;
        private OnServerOffline onServerOffline;
        private Action<Exception> onFatalError;

        public string PlacementServerAddress { get; private set; }
        public long CurrentServerID => this.currentServerInfo.ServerID;

        public PDPlacement(ILoggerFactory loggerFactory)
        {
            this.logger = loggerFactory.CreateLogger("Placement");
        }

        public void SetPlacementServerInfo(string pdAddress)
        {
            if (pdAddress.EndsWith("/"))
            {
                pdAddress = pdAddress.Substring(0, pdAddress.Length - 1);
            }
            if (!pdAddress.StartsWith("http"))
            {
                pdAddress = "http://" + pdAddress;
            }
            this.PlacementServerAddress = pdAddress;

            this.logger.LogInformation("SetPlacementServerInfo, Address:{0}", pdAddress);
        }

        private async Task<ValueTuple<int, string>> GetAsync(string path)
        {
            var url = $"{this.PlacementServerAddress}{path}";
            var response = await this.httpClient.GetAsync(url).ConfigureAwait(false);
            var str = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            return new ValueTuple<int, string>((int)response.StatusCode, str);
        }

        private async Task<ValueTuple<int, string>> PostAsync(string path, object o)
        {
            var url = $"{this.PlacementServerAddress}{path}";
            var response = await this.httpClient.PostAsync(url, o.AsJson()).ConfigureAwait(false);
            var str = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
            return new ValueTuple<int, string>((int)response.StatusCode, str);
        }

        private bool IsServerValid(long serverID)
        {
            return this.host.TryGetValue(serverID, out var _) ||
                   this.offlineServer.Get(serverID) != null;
        }

        public PlacementFindActorPositionResponse FindActorPositionInCache(PlacementFindActorPositionRequest request)
        {
            var uniqueName = $"{request.ActorType}/{request.ActorID}";
            var pos = this.positionLru.Get(uniqueName);
            if (pos != null && this.IsServerValid(pos.ServerID))
            {
                return pos;
            }
            return null;
        }

        public async Task<PlacementFindActorPositionResponse> FindActorPositonAsync(PlacementFindActorPositionRequest request)
        {
            //check actor position cache
            var uniqueName = $"{request.ActorType}/{request.ActorID}";

            var pos = this.positionLru.Get(uniqueName);
            if (pos != null && this.IsServerValid(pos.ServerID))
            {
                return pos;
            }
            this.positionLru.Remove(uniqueName);

            var (code, str) = await this.PostAsync("/pd/api/v1/placement/find_position", request).ConfigureAwait(false);
            if (code != (int)HttpStatusCode.OK)
            {
                this.logger.LogError("FindActorPositionAsync fail, ActorType:{0}, ActorID:{1}, TTL:{2}, ErrorMessage:{3}",
                    request.ActorType, request.ActorID, request.TTL, str);
                throw new PlacementException(code, str);
            }

            var position =  JsonSerializer.Deserialize<PlacementFindActorPositionResponse>(str);

            //如果服务器要下线了, 那么存到LRU里面, 还是需要每次都去重新定位
            if (this.offlineServer.Get(position.ServerID) == null)
            {
                this.positionLru.Add(uniqueName, position);
            }
            return position;
        }

        public class SequenceResponse
        {
            [JsonPropertyName("id")]
            public long ID { get; set; }
        }

        private static readonly object EmptyObject = new Dictionary<string, string>();
        public async Task<long> GenerateNewSequenceAsync(string sequenceType, int step)
        {
            var path = $"/pd/api/v1/id/new_sequence/{sequenceType}/{step}";
            var (code, str) = await this.PostAsync(path, EmptyObject.AsJson()).ConfigureAwait(false);

            if (code != (int)HttpStatusCode.OK)
            {
                this.logger.LogError("GenerateNewSequenceAsync fail, SequenceType:{0}, Step:{1}, ErrorMessage:{3}",
                    sequenceType, step, str);
                throw new PlacementException(code, str);
            }

            var response = JsonSerializer.Deserialize<SequenceResponse>(str);
            return response.ID;
        }

        public async Task<long> GenerateNewTokenAsync()
        {
            var path = "/pd/api/v1/placement/new_token";
            var (code, str) = await this.PostAsync(path, EmptyObject.AsJson()).ConfigureAwait(false);

            if (code != (int)HttpStatusCode.OK)
            {
                this.logger.LogError("GenerateNewTokenAsync fail, ErrorMessage:{0}", str);
                throw new PlacementException(code, str);
            }

            var response = JsonSerializer.Deserialize<SequenceResponse>(str);
            return response.ID;
        }

        public async Task<long> GenerateServerIDAsync()
        {
            var path = "/pd/api/v1/id/new_server_id";
            var (code, str) = await this.PostAsync(path, EmptyObject.AsJson()).ConfigureAwait(false);

            if (code != (int)HttpStatusCode.OK)
            {
                this.logger.LogError("GenerateServerIDAsync fail, ErrorMessage:{0}", str);
                throw new PlacementException(code, str);
            }

            var response = JsonSerializer.Deserialize<SequenceResponse>(str);
            return response.ID;
        }

        public async Task<PlacementKeepAliveResponse> KeepAliveServerAsync(long serverID, long leaseID, long load)
        {
            var path = "/pd/api/v1/membership/keep_alive";
            var (code, str) = await this.PostAsync(path, new PlacementActorHostInfo()
            {
                ServerID = serverID,
                LeaseID = leaseID,
                Load = load,
            }).ConfigureAwait(false);
            if (code != (int)HttpStatusCode.OK)
            {
                this.logger.LogError("KeepAliveServerAsync fail, ErrorMessage:{0}", str);
                throw new PlacementException(code, str);
            }
            var response = JsonSerializer.Deserialize<PlacementKeepAliveResponse>(str);
            return response;
        }

        class RegisterServerResponse
        {
            [JsonPropertyName("lease_id")]
            public long LeaseID { get; set; }
        }

        public async Task<long> RegisterServerAsync(PlacementActorHostInfo info)
        {
            if (info.TTL == 0)
            {
                info.TTL = 15;
            }
            var path = "/pd/api/v1/membership/register";
            var (code, str) = await this.PostAsync(path, info).ConfigureAwait(false);
            if (code != (int)HttpStatusCode.OK)
            {
                this.logger.LogError("RegisterServerAsync fail, ErrorMessage:{0}", str);
                throw new PlacementException(code, str);
            }
            var response = JsonSerializer.Deserialize<RegisterServerResponse>(str);
            if (response.LeaseID != 0)
            {
                this.currentServerInfo.ServerID = info.ServerID;
                this.currentServerInfo.StartTime = info.StartTime;
                this.currentServerInfo.Address = info.Address;
                this.currentServerInfo.Services = info.Services;
                this.currentServerInfo.TTL = info.TTL;

                this.currentServerInfo.LeaseID = response.LeaseID;
                this.logger.LogInformation("RegisterServerAsync success, ServerID:{0}, LeaseID:{1}", info.ServerID, response.LeaseID);
            }
            return response.LeaseID;
        }

        public async Task<PlacementVersionInfo> GetVersionAsync()
        {
            var (code, str) = await this.GetAsync("/pd/api/v1/version").ConfigureAwait(false);

            if (code != (int)HttpStatusCode.OK)
            {
                this.logger.LogError("GetVersion fail, ErrorMessage:{0}", str);
                throw new PlacementException(code, str);
            }

            var position = JsonSerializer.Deserialize<PlacementVersionInfo>(str);
            return position;
        }

        public void RegisterServerChangedEvent(IPlacement.OnAddServer onAddServer, IPlacement.OnRemoveServer onRemoveServer, IPlacement.OnServerOffline onServerOffline)
        {
            this.onAddServer = onAddServer;
            this.onRemoveServer = onRemoveServer;
            this.onServerOffline = onServerOffline;
        }

        public void SetServerLoad(long load)
        {
            this.currentServerInfo.Load = load;
            if (this.logger.IsEnabled(LogLevel.Trace))
            {
                this.logger.LogTrace("UpdateServerLoad, Load:{0}", load);
            }
        }

        private readonly CancellationTokenSource pullingCancelTokenSource = new CancellationTokenSource();

        private async Task PullOnce(CancellationToken cancellationToken)
        {
            if (cancellationToken.IsCancellationRequested) return;
            var response = await this.KeepAliveServerAsync(this.currentServerInfo.ServerID,
                                                            this.currentServerInfo.LeaseID,
                                                            this.currentServerInfo.Load).ConfigureAwait(false);

            if (this.logger.IsEnabled(LogLevel.Trace))
            {
                this.logger.LogTrace("KeepAliveServerAsync response, EventCount: {0}", response.Events.Count);
            }

            var newServerList = response.Hosts;
            foreach (var item in response.Events)
            {
                ProcessAddServerEvent(newServerList, item);
                ProcessRemoveServerEvent(item);
            }
            this.ProcessServerOfflineEvent(newServerList);
            this.ProcessDiffTwoServerList(newServerList);
        }

        private void ProcessDiffTwoServerList(Dictionary<long, PlacementActorHostInfo> newServerList)
        {
            foreach (var (serverID, info) in newServerList)
            {
                if (this.host.ContainsKey(serverID)) continue;
                if (this.addedServer.TryAdd(serverID, EmptyObject))
                {
                    this.logger.LogInformation("PD Add Server, ServerID:{0}", serverID);
                    try
                    {
                        this.onAddServer(info);
                    }
                    catch (Exception e)
                    {
                        this.logger.LogError("OnAddServer Exception:{0}", e.Message);
                    }
                }
            }
            this.host = newServerList;
        }


        private void ProcessServerOfflineEvent(Dictionary<long, PlacementActorHostInfo> newServerList)
        {
            foreach (var (serverID, info) in newServerList)
            {
                if (info.TTL < 0)
                {
                    if (this.offlineServer.TryAdd(serverID, EmptyObject))
                    {
                        try
                        {
                            this.onServerOffline(info);
                        }
                        catch (Exception e)
                        {
                            this.logger.LogError("OnOfflineServer Exception:{0}", e.Message);
                        }
                    }
                }
            }
        }

        private void ProcessAddServerEvent(Dictionary<long, PlacementActorHostInfo> newServerList, PlacementEvents item)
        {
            foreach (var add in item.Add)
            {
                if (this.addedServer.TryAdd(add, EmptyObject))
                {
                    this.logger.LogInformation("PD Add Server, ServerID:{0}", add);
                    if (newServerList.TryGetValue(add, out var s))
                    {
                        try
                        {
                            this.onAddServer(s);
                        }
                        catch (Exception e)
                        {
                            this.logger.LogError("OnAddServer Exception:{0}", e.Message);
                        }
                    }
                }
            }
        }

        private void ProcessRemoveServerEvent(PlacementEvents item)
        {
            foreach (var remove in item.Remove)
            {
                if (this.removedServer.TryAdd(remove, EmptyObject))
                {
                    this.logger.LogInformation("PD Remove Server, ServerID:{0}", remove);
                    if (this.host.TryGetValue(remove, out var s))
                    {
                        try
                        {
                            this.onRemoveServer(s);
                        }
                        catch (Exception e)
                        {
                            this.logger.LogError("OnRemoveServer Exception:{0}", e.Message);
                        }
                    }
                }
            }
        }

        public Task StartPullingAsync()
        {
#pragma warning disable CS4014 // Because this call is not awaited, execution of the current method continues before the call is completed
            var result = Task.Run(async () =>
            {
                var timerInterval = this.currentServerInfo.TTL / 3 * 1000;
                var currentMilliSeconds = Platform.GetMilliSeconds();
                var timerCount = 0;
                var failedCount = 0;
                while (!pullingCancelTokenSource.Token.IsCancellationRequested)
                {
                    try
                    {
                        await this.PullOnce(pullingCancelTokenSource.Token).ConfigureAwait(false);
                        failedCount = 0;
                    }
                    catch (Exception e)
                    {
                        this.logger.LogError("PD KeepAlive PullOnce fail, Exception:{0}", e.Message);
                        if (++failedCount >= 3) 
                        {
                            //这边异常情况, 服务器需要主动退出
                            if (this.onFatalError != null)
                            {
                                this.onFatalError(e);
                            }
                            break;
                        }
                    }
                    finally
                    {
                        timerCount++;
                        var delay = timerCount * timerInterval - (Platform.GetMilliSeconds() - currentMilliSeconds);
                        if (delay > 0)
                        {
                            await Task.Delay((int)delay).ConfigureAwait(false);
                        }
                    }
                }
            });
#pragma warning restore CS4014 // Because this call is not awaited, execution of the current method continues before the call is completed
            return result;
        }

        public Task StopPullingAsync()
        {
            pullingCancelTokenSource.Cancel();
            return Task.FromResult(0);
        }

        public void ClearActorPositionCache(PlacementFindActorPositionRequest request)
        {
            var uniqueName = $"{request.ActorType}/{request.ActorID}";
            this.positionLru.Remove(uniqueName);
            this.logger.LogInformation("ClearActorPosition, UniqueName:{0}", uniqueName);
        }

        public void OnException(Action<Exception> fn)
        {
            this.onFatalError = fn;
        }
    }
}