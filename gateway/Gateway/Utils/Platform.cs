using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace Gateway.Utils
{
    public class Platform
    {
        private static readonly DateTime UTC = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);
        private static long ServerStartSeconds = 0;
        private static long ServerStartMilliSeconds = 0;
        private static long ServerStartTicks = 0;
        private static string LocalIpAddress = "";

        static Platform()
        {
            var now = DateTime.Now;
            ServerStartTicks = Stopwatch.GetTimestamp();
            ServerStartSeconds = (long)TimeZoneInfo.ConvertTimeToUtc(now).Subtract(UTC).TotalSeconds;
            ServerStartMilliSeconds = (long)TimeZoneInfo.ConvertTimeToUtc(now).Subtract(UTC).TotalMilliseconds;
        }

        public static long GetRelativeSeconds(DateTime d)
        {
            return (long)TimeZoneInfo.ConvertTimeToUtc(DateTime.Now).Subtract(d).TotalSeconds;
        }

        public static long GetSeconds()
        {
            var ElapsedSeconds = (Stopwatch.GetTimestamp() - ServerStartTicks) / Stopwatch.Frequency;
            return ServerStartSeconds + ElapsedSeconds;
        }

        public static long GetMilliSeconds()
        {
            var ElapsedMilliSeconds = (Stopwatch.GetTimestamp() - ServerStartTicks) * 1000 / Stopwatch.Frequency;
            return ServerStartMilliSeconds + ElapsedMilliSeconds;
        }


        public static string GetLocalAddresss()
        {
            if (!string.IsNullOrEmpty(LocalIpAddress)) return LocalIpAddress;
            var udpClient = new UdpClient();
            udpClient.Connect("8.8.8.8", 80);
            var localEndPoint = udpClient.Client.LocalEndPoint as IPEndPoint;
            ArgumentNullException.ThrowIfNull(localEndPoint, nameof(localEndPoint));
            LocalIpAddress = localEndPoint.Address.ToString();
            return LocalIpAddress;
        }
    }
}