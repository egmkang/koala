using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using DotNetty.Transport.Channels;
using Gateway.Utils;

namespace Gateway.Network
{
    internal class SendingMessageThread
    {
        private static volatile int Index = 0;
        private readonly object mutex = new object();
        private Dictionary<long, IChannel> channels = new Dictionary<long, IChannel>();
        private Dictionary<long, IChannel> temp = new Dictionary<long, IChannel>();
        private readonly Thread thread;
        private volatile int stop = 0;
        private readonly AtomicInt64 pendingCount = new AtomicInt64();

        public SendingMessageThread() 
        {
            this.thread = new Thread(this.SendingLoop);
            this.thread.Name = $"SendingMessageThread_{Index++}";
            this.thread.Start();
        }

        public void SendMessage(IChannel channel) 
        {
            var sessionInfo = channel.GetSessionInfo();
            lock (this.mutex) 
            {
                channels.TryAdd(sessionInfo.SessionID, channel);
                pendingCount.Inc();
                Monitor.Pulse(this.mutex);
            }
        }

        public void SendingLoop() 
        {
            while (stop == 0) 
            {
                while (true)
                {
                    lock (this.mutex)
                    {
                        var count = this.pendingCount.Load();
                        if (count == 0)
                        {
                            Monitor.Wait(this.mutex);
                            continue;
                        }
                        var t = this.channels;
                        channels = temp;
                        temp = t;
                        this.channels.Clear();
                        this.pendingCount.Add(-count);
                        break;
                    }
                }

                foreach (var (_, channel) in temp) 
                {
                    var sessionInfo = channel.GetSessionInfo();
                    sessionInfo.SendMessagesBatch(channel);
                }
            }
        }
    }

    public class SendingThreads
    {
        const int SendThreadCount = 2;
        private readonly SendingMessageThread[] array = new SendingMessageThread[SendThreadCount] { new SendingMessageThread(), new SendingMessageThread() };

        public void SendMessage(IChannel channel) 
        {
            if (channel == null) return;
            var sessionInfo = channel.GetSessionInfo();
            if (sessionInfo == null) return;

            array[sessionInfo.SessionID % SendThreadCount].SendMessage(channel);
        }
    }
}
