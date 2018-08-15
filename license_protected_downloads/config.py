# Configuration file for linaro-license-protection

# Let internal hosts through always.
INTERNAL_HOSTS = (
    '82.71.243.201',   # validation.linaro.org
    '82.71.243.203',
    '51.148.40.1',
    '51.148.40.7',
    '81.128.185.42',   # tcwg.validation.linaro.org
    '81.128.185.50',   # lab.validation.linaro.org
    '81.128.185.52',   # lng.validation.linaro.org
    '144.76.6.139',    # aosp-x86_64-07
    '188.40.51.209',   # aosp-x86_64-08
    '213.133.116.86',  # aosp-x86_64-09 (ART)
    '78.46.190.194',   # aosp-x86_64-10 (ART)
    '148.251.140.195', # lhg-build-01
    '188.40.92.79',    # x86_64-07
    '188.40.49.144',   # x86_64-08
    '148.251.184.94',  # x86_64-09
    '138.201.52.83',   # x86_64-10
    '88.99.28.12',     # x86_64-11 (RPB)
    '88.99.28.38',     # x86_64-12 (RPB)
    '88.99.59.232',    # x86_64-13 (LITE)
    '88.99.149.141',   # x86_64-14
    '51.15.185.142',   # lkft-build-01
    '62.210.248.69',   # oe-x86_64-01
    '62.210.249.170',  # oe-x86_64-02
    '217.140.96.140',  # cambridge.arm.com
    '217.140.106.49',  # Cambridge ARM
    '217.140.106.50',  #
    '217.140.106.51',  #
    '217.140.106.52',  #
    '217.140.106.53',  #
    '217.140.106.54',  #
    '217.140.106.55',  #
    '73.14.250.225',   # Tyler's lab - nwdrone.com
    '73.14.250.226',   #
    '73.14.250.227',   #
    '73.14.250.228',   #
    '73.14.250.229',   #
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
