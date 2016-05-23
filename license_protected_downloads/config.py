# Configuration file for linaro-license-protection

# Let internal hosts through always.
INTERNAL_HOSTS = (
    '54.225.81.132',  # android-build.linaro.org
    '82.71.243.201',  # validation.linaro.org
    '82.71.243.203',
    '81.128.185.42',  # tcwg.validation.linaro.org
    '81.128.185.50',  # lab.validation.linaro.org
    '81.128.185.52',  # lng.validation.linaro.org
    '188.40.92.79',   # ci.linaro.org (slave x86-64-07)
    '188.40.49.144',  # ci.linaro.org (slave x86-64-08)
    '144.76.6.139',   # ci.linaro.org (slave aosp-x86-64-07)
    '188.40.51.209',  # ci.linaro.org (slave aosp-x86-64-08)
    '213.133.116.86', # ci.linaro.org (slave aosp-x86-64-09)
    '78.46.190.194',  # ci.linaro.org (slave aosp-x86-64-10)
    '217.140.96.140', # cambridge.arm.com
    '73.14.250.225', # Tyler's lab - nwdrone.com
    '73.14.250.226', # 
    '73.14.250.227', # 
    '73.14.250.228', # 
    '73.14.250.229', # 
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
