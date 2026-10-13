using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace DAIApplication
{
    public class DAIApp : Form
    {
        [DllImport("user32.dll")]
        private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

        [DllImport("user32.dll")]
        private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        [DllImport("user32.dll")]
        private static extern bool BringWindowToTop(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern bool EnumDesktopWindows(IntPtr hDesktop, EnumWindowsProc filter, IntPtr lParam);

        [DllImport("user32.dll")]
        private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        [DllImport("user32.dll")]
        private static extern int GetClassName(IntPtr hWnd, StringBuilder text, int count);

        [DllImport("user32.dll")]
        private static extern bool IsWindowVisible(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

        [DllImport("kernel32.dll")]
        private static extern uint GetCurrentThreadId();

        [DllImport("user32.dll")]
        private static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);

        private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        private const int HOTKEY_ID = 9001;
        private const uint MOD_ALT = 0x0001;
        private const uint MOD_CONTROL = 0x0002;
        private const uint MOD_NOREPEAT = 0x4000;
        private const uint VK_D = 0x44;
        private const int WM_HOTKEY = 0x0312;
        private const int SW_RESTORE = 9;
        private const int SW_MINIMIZE = 6;

        private static string ProjectDir = @"C:\Users\hp\Desktop\DAI";
        private static string BackendDir = Path.Combine(ProjectDir, "backend");
        private static string FrontendDir = Path.Combine(ProjectDir, "frontend");
        private static string PythonExe = Path.Combine(BackendDir, @".venv\Scripts\python.exe");
        private static string NodeExe = @"C:\Program Files\nodejs\node.exe";
        private static string NextBin = Path.Combine(FrontendDir, @"node_modules\next\dist\bin\next");
        private static string ChromeExe = @"C:\Program Files\Google\Chrome\Application\chrome.exe";
        private static string EdgeExe = @"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe";
        private static string DataDir = @"C:\Users\hp\AppData\Local\DAI_App_Data";
        private static string AppUrl = "http://localhost:3000/chat";
        private static string IconPath = Path.Combine(ProjectDir, @"desktop_app\dai.ico");

        private NotifyIcon trayIcon;
        private ContextMenu trayMenu;

        public DAIApp(bool startMinimized)
        {
            this.ShowInTaskbar = false;
            this.WindowState = FormWindowState.Minimized;
            this.FormBorderStyle = FormBorderStyle.None;
            this.Size = new Size(0, 0);

            // 1. Setup System Tray
            SetupTray();

            // 2. Register Global Hotkey (Alt + D)
            RegisterHotKey(this.Handle, HOTKEY_ID, MOD_ALT | MOD_NOREPEAT, VK_D);

            // 3. Ensure Backend & Frontend
            new Thread(EnsureServers).Start();

            // 4. Open Window if not startMinimized
            if (!startMinimized)
            {
                new Thread(LaunchAppWindow).Start();
            }
        }

        private void SetupTray()
        {
            trayMenu = new ContextMenu();
            trayMenu.MenuItems.Add("Open DAI (Alt+D)", (s, e) => ToggleOrFocus(true));
            trayMenu.MenuItems.Add("Toggle Window", (s, e) => ToggleOrFocus(false));
            trayMenu.MenuItems.Add("-");
            trayMenu.MenuItems.Add("Exit DAI", (s, e) => ExitApplication());

            trayIcon = new NotifyIcon();
            trayIcon.Text = "DAI - Personal AI Assistant (Alt+D)";
            try
            {
                if (File.Exists(IconPath))
                    trayIcon.Icon = new Icon(IconPath);
                else
                    trayIcon.Icon = SystemIcons.Application;
            }
            catch
            {
                trayIcon.Icon = SystemIcons.Application;
            }

            trayIcon.ContextMenu = trayMenu;
            trayIcon.Visible = true;
            trayIcon.DoubleClick += (s, e) => ToggleOrFocus(true);
        }

        private static bool IsPortOpen(int port)
        {
            try
            {
                using (TcpClient client = new TcpClient())
                {
                    IAsyncResult result = client.BeginConnect("127.0.0.1", port, null, null);
                    bool success = result.AsyncWaitHandle.WaitOne(300);
                    if (!success) return false;
                    client.EndConnect(result);
                    return true;
                }
            }
            catch
            {
                return false;
            }
        }

        private static void EnsureServers()
        {
            // Backend
            if (!IsPortOpen(8000))
            {
                ProcessStartInfo beInfo = new ProcessStartInfo
                {
                    FileName = PythonExe,
                    Arguments = "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",
                    WorkingDirectory = BackendDir,
                    CreateNoWindow = true,
                    UseShellExecute = false
                };
                try { Process.Start(beInfo); } catch { }
            }

            // Frontend (Standalone Production Build)
            if (!IsPortOpen(3000))
            {
                string prodBuild = Path.Combine(FrontendDir, ".next");
                string cmdArgs = File.Exists(Path.Combine(prodBuild, "standalone", "server.js"))
                    ? string.Format("\"{0}\"", Path.Combine(prodBuild, "standalone", "server.js"))
                    : string.Format("\"{0}\" start -p 3000", NextBin);

                ProcessStartInfo feInfo = new ProcessStartInfo
                {
                    FileName = File.Exists(NodeExe) ? NodeExe : "node",
                    Arguments = cmdArgs,
                    WorkingDirectory = FrontendDir,
                    CreateNoWindow = true,
                    UseShellExecute = false
                };
                try { Process.Start(feInfo); } catch { }
            }

            // Wait up to 6 seconds for servers to respond
            for (int i = 0; i < 20; i++)
            {
                if (IsPortOpen(3000) && IsPortOpen(8000)) break;
                Thread.Sleep(300);
            }
        }

        private static IntPtr FindDaiWindow()
        {
            IntPtr found = IntPtr.Zero;

            EnumDesktopWindows(IntPtr.Zero, delegate (IntPtr hWnd, IntPtr lParam)
            {
                if (!IsWindowVisible(hWnd)) return true;

                StringBuilder classBuff = new StringBuilder(256);
                GetClassName(hWnd, classBuff, 256);
                string className = classBuff.ToString();
                if (className != "Chrome_WidgetWin_1") return true;

                StringBuilder titleBuff = new StringBuilder(256);
                GetWindowText(hWnd, titleBuff, 256);
                string title = titleBuff.ToString().ToLower();

                // Reject other tools
                if (title.Contains("chatgpt") || title.Contains("visual studio") || title.Contains("code") ||
                    title.Contains("whatsapp") || title.Contains("linkedin"))
                {
                    return true;
                }

                if (title == "dai" || title.StartsWith("dai -") || title.Contains("personal ai assistant") || title.Contains("localhost:3000"))
                {
                    found = hWnd;
                    return false; // Stop enumeration
                }

                return true;
            }, IntPtr.Zero);

            return found;
        }

        private static void ForceForeground(IntPtr hWnd)
        {
            try
            {
                ShowWindow(hWnd, SW_RESTORE);
                IntPtr fgHwnd = GetForegroundWindow();
                if (fgHwnd != hWnd)
                {
                    uint fgTid;
                    GetWindowThreadProcessId(fgHwnd, out fgTid);
                    uint curTid = GetCurrentThreadId();

                    if (fgTid != 0 && fgTid != curTid)
                    {
                        AttachThreadInput(curTid, fgTid, true);
                        SetForegroundWindow(hWnd);
                        BringWindowToTop(hWnd);
                        AttachThreadInput(curTid, fgTid, false);
                    }
                    else
                    {
                        SetForegroundWindow(hWnd);
                        BringWindowToTop(hWnd);
                    }
                }
            }
            catch
            {
                ShowWindow(hWnd, SW_RESTORE);
                SetForegroundWindow(hWnd);
            }
        }

        private static void LaunchAppWindow()
        {
            EnsureServers();

            string browserExe = File.Exists(ChromeExe) ? ChromeExe : (File.Exists(EdgeExe) ? EdgeExe : null);
            if (browserExe != null)
            {
                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = browserExe,
                    Arguments = string.Format("--app={0} --user-data-dir=\"{1}\" --window-size=1280,840", AppUrl, DataDir),
                    UseShellExecute = true
                };
                try { Process.Start(psi); } catch { }
            }
            else
            {
                try { Process.Start(AppUrl); } catch { }
            }
        }

        public static void ToggleOrFocus(bool forceOpen)
        {
            IntPtr hwnd = FindDaiWindow();
            IntPtr fgHwnd = GetForegroundWindow();

            if (hwnd != IntPtr.Zero)
            {
                if (forceOpen)
                {
                    ForceForeground(hwnd);
                }
                else if (fgHwnd == hwnd)
                {
                    ShowWindow(hwnd, SW_MINIMIZE);
                }
                else
                {
                    ForceForeground(hwnd);
                }
            }
            else
            {
                new Thread(LaunchAppWindow).Start();
            }
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_HOTKEY)
            {
                ToggleOrFocus(false);
            }
            base.WndProc(ref m);
        }

        private void ExitApplication()
        {
            try
            {
                UnregisterHotKey(this.Handle, HOTKEY_ID);
                if (trayIcon != null)
                {
                    trayIcon.Visible = false;
                    trayIcon.Dispose();
                }
            }
            catch { }
            Application.Exit();
            Environment.Exit(0);
        }

        [STAThread]
        public static void Main(string[] args)
        {
            bool createdNew;
            using (Mutex mutex = new Mutex(true, "Global\\DAI_Native_App_Mutex_2026", out createdNew))
            {
                if (!createdNew)
                {
                    // Existing instance running -> focus window and exit
                    ToggleOrFocus(true);
                    return;
                }

                bool startMinimized = args.Length > 0 && args[0] == "--minimized";

                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new DAIApp(startMinimized));
            }
        }
    }
}
