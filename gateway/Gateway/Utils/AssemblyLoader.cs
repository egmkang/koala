using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.Loader;
using System.Text;

namespace Gateway.Utils
{
    public class AssemblyLoader
    {
        private static List<string> FindFilesInPath(string dir) 
        {
            var list = new List<string>();
            foreach (var file in Directory.GetFiles(dir)) 
            {
                if (file.EndsWith(".dll")) 
                {
                    list.Add(file);
                }
            }
            return list;
        }

        private static bool IsAssemblyLoaded(string fileName)
        {
            var assemblies = AppDomain.CurrentDomain.GetAssemblies();
            foreach (var asm in assemblies)
            {
                try
                {
                    if (asm.Location == fileName) return true;
                }
                catch { }
            }
            return false;
        }

        public static void LoadAssemblies()
        {
            var dir = Directory.GetCurrentDirectory();

            var files = FindFilesInPath(dir);
            foreach (var file in files) 
            {
                if (IsAssemblyLoaded(file)) continue;
                try
                {
                    var asm = AssemblyLoadContext.Default.LoadFromAssemblyPath(file);
                }
                catch (Exception e) 
                {
                    Console.WriteLine("Load Assembly, File:{0}, Exception:{1}", file, e);
                }
            }
        }
    }
}
