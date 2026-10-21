using Microsoft.UI.Xaml;
using Microsoft.Windows.AppLifecycle;

namespace SmartSearch.Desktop;

public partial class App : Application
{
    private static Window? _window;
    private static Mutex? _singleInstanceMutex;
    private static AppInstance? _mainInstance;

    public App()
    {
        InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
#if DEBUG
        ProtocolSelfTest.Run();
#endif
        _window ??= new MainWindow();
        _window.Activate();
    }

    internal static void SetSingleInstance(Mutex mutex, AppInstance instance)
    {
        _singleInstanceMutex = mutex;
        _mainInstance = instance;
        instance.Activated += OnRedirectedActivation;
    }

    internal static void ReleaseInstallerMutex()
    {
        _singleInstanceMutex?.Dispose();
        _singleInstanceMutex = null;
    }

    internal static void RestoreInstallerMutex() =>
        _singleInstanceMutex ??= new Mutex(initiallyOwned: false, Program.MutexName);

    private static void OnRedirectedActivation(object? sender, AppActivationArguments args)
    {
        if (_window is MainWindow window)
            window.DispatcherQueue.TryEnqueue(window.ActivateFromRedirect);
    }
}
