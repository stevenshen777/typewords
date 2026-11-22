// TypeWords 桌面版启动器：内嵌静态站点，启动本地 HTTP 服务并打开浏览器
// 编译：csc /target:exe /resource:payload.zip（见 build-exe.mjs）
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Text;
using System.Threading;

class TypeWordsLauncher
{
    static Dictionary<string, byte[]> files = new Dictionary<string, byte[]>();
    static string root = "";

    static void Main(string[] args)
    {
        try { Console.OutputEncoding = Encoding.UTF8; } catch { }
        Console.Title = "TypeWords 桌面版";

        Console.WriteLine("TypeWords 桌面版 - 正在加载资源...");
        files = LoadPayload();

        int port = FindFreePort(5567, 5600);
        if (port < 0)
        {
            Console.WriteLine("没有可用端口，程序退出。请关闭占用 5567-5600 的程序后重试。");
            Console.WriteLine("按任意键退出...");
            Console.ReadKey();
            return;
        }

        TcpListener listener = new TcpListener(IPAddress.Loopback, port);
        listener.Start();
        root = "http://127.0.0.1:" + port + "/";

        Thread accept = new Thread(delegate () { AcceptLoop(listener); });
        accept.IsBackground = true;
        accept.Start();

        Console.WriteLine("");
        Console.WriteLine("  本地地址: " + root);
        Console.WriteLine("  已自动打开浏览器；若未打开请手动复制上面的地址访问。");
        Console.WriteLine("  关闭此窗口即停止服务并退出程序。");
        Console.WriteLine("");

        try { Process.Start(root); } catch { }
        while (true) Thread.Sleep(2000);
    }

    static Dictionary<string, byte[]> LoadPayload()
    {
        Dictionary<string, byte[]> map = new Dictionary<string, byte[]>();
        Assembly asm = Assembly.GetExecutingAssembly();
        Stream res = null;
        foreach (string name in asm.GetManifestResourceNames())
        {
            if (name.EndsWith("payload.zip", StringComparison.OrdinalIgnoreCase))
            {
                res = asm.GetManifestResourceStream(name);
                break;
            }
        }
        if (res == null)
        {
            Console.WriteLine("资源缺失：未找到内嵌 payload.zip");
            return map;
        }
        using (ZipArchive zip = new ZipArchive(res, ZipArchiveMode.Read))
        {
            foreach (ZipArchiveEntry entry in zip.Entries)
            {
                if (entry.Name.Length == 0) continue; // 目录项
                using (Stream s = entry.Open())
                {
                    MemoryStream ms = new MemoryStream();
                    s.CopyTo(ms);
                    string key = NormalizeKey(entry.FullName);
                    map[key] = ms.ToArray();
                }
            }
        }
        Console.WriteLine("已加载 " + map.Count + " 个文件");
        return map;
    }

    static string NormalizeKey(string p)
    {
        p = p.Replace('\\', '/');
        while (p.Contains("//")) p = p.Replace("//", "/");
        return p.TrimStart('/').ToLowerInvariant();
    }

    static int FindFreePort(int start, int end)
    {
        for (int p = start; p <= end; p++)
        {
            try
            {
                TcpListener t = new TcpListener(IPAddress.Loopback, p);
                t.Start();
                t.Stop();
                return p;
            }
            catch { }
        }
        return -1;
    }

    static void AcceptLoop(TcpListener listener)
    {
        while (true)
        {
            TcpClient client = null;
            try
            {
                client = listener.AcceptTcpClient();
            }
            catch
            {
                return;
            }
            TcpClient c = client;
            ThreadPool.QueueUserWorkItem(delegate (object state) { Handle(c); });
        }
    }

    static void Handle(TcpClient client)
    {
        try
        {
            using (client)
            {
                client.ReceiveTimeout = 5000;
                client.SendTimeout = 5000;
                NetworkStream ns = client.GetStream();

                string requestLine = ReadRequestLine(ns);
                if (requestLine == null)
                {
                    return;
                }

                string[] parts = requestLine.Split(' ');
                string method = parts.Length > 0 ? parts[0].ToUpperInvariant() : "GET";
                string rawPath = parts.Length > 1 ? parts[1] : "/";
                if (method != "GET" && method != "HEAD")
                {
                    WriteText(ns, "405 Method Not Allowed", "text/plain; charset=utf-8", Encoding.UTF8.GetBytes("Method Not Allowed"), false);
                    return;
                }

                int q = rawPath.IndexOf('?');
                if (q >= 0) rawPath = rawPath.Substring(0, q);
                string path;
                try { path = Uri.UnescapeDataString(rawPath); }
                catch { path = rawPath; }

                Serve(ns, method, path);
            }
        }
        catch { }
    }

    static string ReadRequestLine(NetworkStream ns)
    {
        byte[] buf = new byte[8192];
        int total = 0;
        while (total < buf.Length)
        {
            int n;
            try { n = ns.Read(buf, total, buf.Length - total); }
            catch { return null; }
            if (n <= 0) return null;
            total += n;
            string text = Encoding.ASCII.GetString(buf, 0, total);
            int headEnd = text.IndexOf("\r\n\r\n");
            if (headEnd >= 0)
            {
                int lineEnd = text.IndexOf("\r\n");
                if (lineEnd < 0) return text.Substring(0, headEnd);
                return text.Substring(0, lineEnd);
            }
        }
        return null;
    }

    static void Serve(NetworkStream ns, string method, string path)
    {
        if (path.Contains("..")) { WriteText(ns, "403 Forbidden", "text/plain; charset=utf-8", Encoding.UTF8.GetBytes("Forbidden"), method == "HEAD"); return; }

        string key = NormalizeKey(path);
        if (key.Length == 0) key = "index.html";
        if (key.EndsWith("/")) key = key + "index.html";

        byte[] body = null;
        if (files.ContainsKey(key)) body = files[key];
        else if (!HasExtension(key))
        {
            // SPA 路由回退
            string idx = "index.html";
            if (files.ContainsKey(idx)) body = files[idx];
        }

        if (body == null)
        {
            WriteText(ns, "404 Not Found", "text/plain; charset=utf-8", Encoding.UTF8.GetBytes("404 Not Found"), method == "HEAD");
            return;
        }

        bool immutable = key.StartsWith("_nuxt/");
        string cache = immutable ? "public, max-age=31536000, immutable" : "no-cache";
        WriteText(ns, "200 OK", ContentTypeOf(key), body, method == "HEAD", cache);
    }

    static bool HasExtension(string key)
    {
        int slash = key.LastIndexOf('/');
        string name = slash >= 0 ? key.Substring(slash + 1) : key;
        return name.LastIndexOf('.') > 0;
    }

    static string ContentTypeOf(string key)
    {
        string ext = "";
        int dot = key.LastIndexOf('.');
        if (dot >= 0) ext = key.Substring(dot).ToLowerInvariant();
        switch (ext)
        {
            case ".html": return "text/html; charset=utf-8";
            case ".js":
            case ".mjs": return "application/javascript; charset=utf-8";
            case ".css": return "text/css; charset=utf-8";
            case ".json":
            case ".map": return "application/json; charset=utf-8";
            case ".svg": return "image/svg+xml";
            case ".png": return "image/png";
            case ".jpg":
            case ".jpeg": return "image/jpeg";
            case ".webp": return "image/webp";
            case ".gif": return "image/gif";
            case ".ico": return "image/x-icon";
            case ".wav": return "audio/wav";
            case ".mp3": return "audio/mpeg";
            case ".ogg": return "audio/ogg";
            case ".woff": return "font/woff";
            case ".woff2": return "font/woff2";
            case ".ttf": return "font/ttf";
            case ".otf": return "font/otf";
            case ".wasm": return "application/wasm";
            case ".txt": return "text/plain; charset=utf-8";
            case ".pdf": return "application/pdf";
            default: return "application/octet-stream";
        }
    }

    static void WriteText(NetworkStream ns, string status, string contentType, byte[] body, bool headOnly)
    {
        WriteText(ns, status, contentType, body, headOnly, "no-cache");
    }

    static void WriteText(NetworkStream ns, string status, string contentType, byte[] body, bool headOnly, string cache)
    {
        StringBuilder sb = new StringBuilder();
        sb.Append("HTTP/1.1 ").Append(status).Append("\r\n");
        sb.Append("Content-Type: ").Append(contentType).Append("\r\n");
        sb.Append("Content-Length: ").Append(body.Length).Append("\r\n");
        sb.Append("Cache-Control: ").Append(cache).Append("\r\n");
        sb.Append("Access-Control-Allow-Origin: *\r\n");
        sb.Append("Connection: close\r\n\r\n");
        byte[] head = Encoding.UTF8.GetBytes(sb.ToString());
        ns.Write(head, 0, head.Length);
        if (!headOnly && body.Length > 0) ns.Write(body, 0, body.Length);
        ns.Flush();
    }
}
