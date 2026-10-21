// A universal entry point for the two intact PyInstaller onedir distributions.
#include <errno.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#if defined(__arm64__)
#define BACKEND_ARCH "arm64"
#elif defined(__x86_64__)
#define BACKEND_ARCH "x86_64"
#else
#error Unsupported macOS architecture
#endif

int main(int argc, char *argv[]) {
    (void)argc;
    char executable[PATH_MAX];
    char resolved[PATH_MAX];
    uint32_t size = sizeof(executable);
    if (_NSGetExecutablePath(executable, &size) != 0 || realpath(executable, resolved) == NULL) {
        fprintf(stderr, "Cannot locate the bundled Smart Search backend.\n");
        return 1;
    }
    char *separator = strrchr(resolved, '/');
    if (separator == NULL) {
        return 1;
    }
    *separator = '\0';
    int length = snprintf(executable, sizeof(executable), "%s/%s/smart-search", resolved, BACKEND_ARCH);
    if (length < 0 || (size_t)length >= sizeof(executable)) {
        fprintf(stderr, "Bundled backend path is too long.\n");
        return 1;
    }
    argv[0] = executable;
    execv(executable, argv);
    fprintf(stderr, "Cannot start the %s backend: %s\n", BACKEND_ARCH, strerror(errno));
    return 1;
}
