# Configuration file for linaro-license-protection

# Let internal hosts through always.
INTERNAL_HOSTS = (
    '54.225.81.132'   # android-build.linaro.org
    '81.128.185.50',  # lab.validation.linaro.org
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
