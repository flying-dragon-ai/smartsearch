using System.Globalization;
using System.Reflection;
using System.Text.Json;

namespace SmartSearch.Desktop;

internal static class Localization
{
    private static readonly Dictionary<string, string[]> Messages = Load();
    public static string Preference { get; set; } = "auto";
    public static string Language => Preference is "zh" or "en" ? Preference
        : CultureInfo.CurrentUICulture.TwoLetterISOLanguageName == "zh" ? "zh" : "en";

    public static string L(string source, params object?[] arguments)
    {
        var text = Messages.TryGetValue(source, out var pair) ? pair[Language == "zh" ? 0 : 1] : source;
        return arguments.Length == 0 ? text : string.Format(CultureInfo.CurrentCulture, text, arguments);
    }

    private static Dictionary<string, string[]> Load()
    {
        using var stream = Assembly.GetExecutingAssembly().GetManifestResourceStream("SmartSearch.Localizations.json");
        return stream is null ? [] : JsonSerializer.Deserialize<Dictionary<string, string[]>>(stream) ?? [];
    }
}
