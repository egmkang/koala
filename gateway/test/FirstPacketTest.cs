using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Gateway;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace test
{
    [TestClass]
    public class FirstPacketTest
    {
        [TestMethod]
        public void Decode() 
        {
            ReadOnlySpan<byte> firstPacket = Encoding.UTF8.GetBytes("{\"open_id\":\"1\", \"server_id\":2, \"timestamp\":1212121}");

            var message = firstPacket.DecodeFirstMessage();

            Assert.AreEqual("1", message["open_id"].ToString());
            Assert.AreEqual("2", message["server_id"].ToString());
            Assert.AreEqual("1212121", message["timestamp"].ToString());
        }

        [TestMethod]
        public void ComputeHash() 
        {
            string privateKey = "1234567890";

            ReadOnlySpan<byte> firstPacket = Encoding.UTF8.GetBytes("{\"open_id\":\"1\", \"server_id\":2, \"timestamp\":1212121, \"check_sum\":\"2b3c2c4505f72edccbae6accbde6f1293e7c8a39f2508a032eab616402bbac3b\"}");

            var message = firstPacket.DecodeFirstMessage();

            Assert.IsTrue(message.ComputeHash(privateKey));
        }
    }
}
