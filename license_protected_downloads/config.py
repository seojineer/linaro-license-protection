# Configuration file for linaro-license-protection

# Let internal hosts through always.
INTERNAL_HOSTS = (
    '54.225.81.132',  # android-build.linaro.org
    '81.128.185.50',  # lab.validation.linaro.org
    '188.40.92.79',   # ci.linaro.org (slave x86-64-07)
    '188.40.49.144',  # ci.linaro.org (slave x86-64-08)
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
