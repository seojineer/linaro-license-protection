# Configuration file for linaro-license-protection

# Let internal hosts through always.
INTERNAL_HOSTS = (
    '50.17.250.69',  # android-build.linaro.org
    '88.98.47.97',  # validation.linaro.org
)

WHITELIST = (
    '/hwpacks',
    '/precise/restricted',
    '/hwpacks/freescale',
    '/hwpacks/samsung',
    '/hwpacks/ste',
    '/hwpacks/ti',
    '/hwpacks/arm',
    '/android/~linaro-android-restricted',
)
