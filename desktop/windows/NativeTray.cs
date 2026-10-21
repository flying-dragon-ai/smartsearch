using System.Runtime.InteropServices;

namespace SmartSearch.Desktop;

internal sealed class NativeTray : IDisposable
{
    private const uint NimAdd = 0x00000000;
    private const uint NimDelete = 0x00000002;
    private const uint NifMessage = 0x00000001;
    private const uint NifIcon = 0x00000002;
    private const uint NifTip = 0x00000004;
    private const int GwlWndProc = -4;
    private const int WmLButtonUp = 0x0202;
    private const int WmLButtonDblClk = 0x0203;
    private readonly nint _windowHandle;
    private readonly uint _callbackMessage;
    private readonly WndProc _windowProcedure;
    private readonly nint _previousWindowProcedure;
    private NotifyIconData _icon;
    private nint _loadedIcon;
    private bool _visible;

    public NativeTray(nint windowHandle, Action showWindow)
    {
        _windowHandle = windowHandle;
        _callbackMessage = RegisterWindowMessage($"SmartSearch.Tray.{Guid.NewGuid():N}");
        _windowProcedure = (hWnd, message, wParam, lParam) =>
        {
            if (message == _callbackMessage && (lParam.ToInt64() == WmLButtonUp || lParam.ToInt64() == WmLButtonDblClk))
                showWindow();
            return CallWindowProc(_previousWindowProcedure, hWnd, message, wParam, lParam);
        };
        _previousWindowProcedure = SetWindowLongPtr(_windowHandle, GwlWndProc, Marshal.GetFunctionPointerForDelegate(_windowProcedure));
        _loadedIcon = LoadImage(nint.Zero, Path.Combine(AppContext.BaseDirectory, "Assets", "smart-search.ico"), 1, 0, 0, 0x10 | 0x40);
        _icon = new NotifyIconData
        {
            cbSize = Marshal.SizeOf<NotifyIconData>(),
            hWnd = _windowHandle,
            uID = 1,
            uFlags = NifMessage | NifIcon | NifTip,
            uCallbackMessage = _callbackMessage,
            hIcon = _loadedIcon != nint.Zero ? _loadedIcon : LoadIcon(nint.Zero, new nint(32512)),
            szTip = "Smart Search"
        };
    }

    public void Show()
    {
        if (!_visible)
            _visible = ShellNotifyIcon(NimAdd, ref _icon);
    }

    public void Hide()
    {
        if (_visible)
        {
            ShellNotifyIcon(NimDelete, ref _icon);
            _visible = false;
        }
    }

    public void Dispose()
    {
        Hide();
        if (_loadedIcon != nint.Zero)
        {
            DestroyIcon(_loadedIcon);
            _loadedIcon = nint.Zero;
        }
        if (_previousWindowProcedure != nint.Zero)
            SetWindowLongPtr(_windowHandle, GwlWndProc, _previousWindowProcedure);
    }

    private delegate nint WndProc(nint hWnd, uint message, nint wParam, nint lParam);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct NotifyIconData
    {
        public int cbSize;
        public nint hWnd;
        public uint uID;
        public uint uFlags;
        public uint uCallbackMessage;
        public nint hIcon;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 128)] public string szTip;
        public uint dwState;
        public uint dwStateMask;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 256)] public string szInfo;
        public uint uTimeoutOrVersion;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 64)] public string szInfoTitle;
        public uint dwInfoFlags;
        public Guid guidItem;
        public nint hBalloonIcon;
    }

    [DllImport("shell32.dll", EntryPoint = "Shell_NotifyIconW", CharSet = CharSet.Unicode)]
    private static extern bool ShellNotifyIcon(uint message, ref NotifyIconData data);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern uint RegisterWindowMessage(string value);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern nint LoadIcon(nint instance, nint iconName);

    [DllImport("user32.dll", EntryPoint = "LoadImageW", CharSet = CharSet.Unicode)]
    private static extern nint LoadImage(nint instance, string name, uint type, int width, int height, uint flags);

    [DllImport("user32.dll")]
    private static extern bool DestroyIcon(nint icon);

    [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW", SetLastError = true)]
    private static extern nint SetWindowLongPtr(nint hWnd, int index, nint newValue);

    [DllImport("user32.dll", EntryPoint = "CallWindowProcW", SetLastError = true)]
    private static extern nint CallWindowProc(nint previous, nint hWnd, uint message, nint wParam, nint lParam);
}
