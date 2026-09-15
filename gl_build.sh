source /opt/fsl-imx-xwayland/6.12-walnascar/environment-setup-armv8a-poky-linux
#source /workstation/opt-toolchain/fsl-imx-xwayland/6.12-walnascar/environment-setup-armv8a-poky-linux
export ARCH=arm64
make distclean
#make imx8mp_evk_defconfig
#make imx8mp_debix_model_a_defconfig 

#make imx95_19x19_evk_defconfig
#make imx95_debix_emb_01_defconfig 

#make imx91_debix_bmb_13_a1_defconfig
#make imx91_debix_bmb_13_a2_defconfig
#make imx93_debix_bmb_13_a1_defconfig
make imx93_debix_bmb_13_a2_defconfig

#HOSTLDFLAGS="-ldl -lpthread" make -j32
make -j32
