### System SDK Download
- Ubuntu 22.04 :
     https://github.com/nxp-imx/meta-nxp-desktop
- Yocto-Linux 5.15.71_2.2.0
     https://www.nxp.com/design/software/embedded-software/i-mx-software/embedded-linux-for-i-mx-applications-processors:IMXLINUX?
   
### Modify sources/meta-imx/meta-bsp/recipes-bsp/u-boot/u-boot-imx_2021.04.bb
    UBOOT_SRC ?= "git://github.com/debix-tech/uboot.git;protocol=https"
    SRCREV = "2e3dc3a2f04e03176eda927e4602048cb4e9382d"

### Build yocto
    DISTRO=imx-desktop-xwayland MACHINE=imx8mpevk source imx-setup-desktop.sh -b debix-desktop
    bitbake -c compile -f -v u-boot-imx
    bitbake -c deploy -f -v u-boot-imx
    bitbake -c compile -f -v imx-boot
    bitbake -c deploy -f -v imx-boot

uboot bin file: debix-desktop/tmp/deploy/images/imx8mpevk/imx-boot-imx8mpevk-sd.bin-flash_evk

### Use ubuntu dd command write to device
    sudo dd if=imx-boot-imx8mpevk-sd.bin-flash_evk of=/dev/sdx bs=1k seek=32 conv=fsync
   
