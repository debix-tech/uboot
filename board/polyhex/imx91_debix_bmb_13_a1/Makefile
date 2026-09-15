#
# Copyright 2024 NXP
#
# SPDX-License-Identifier:      GPL-2.0+
#

obj-y += imx91_debix_bmb_13_a1.o
obj-y += ../../freescale/common/

ifdef CONFIG_XPL_BUILD
obj-y += spl.o
ifdef CONFIG_IMX9_DRAM_INLINE_ECC
obj-$(CONFIG_IMX91_EVK_LPDDR4) += lpddr4_timing_2400mts_ecc.o lpddr4_timing_1600mts_ecc.o
else
#obj-$(CONFIG_IMX91_EVK_LPDDR4) += lpddr4_timing_2400mts.o lpddr4_timing_1600mts.o
obj-$(CONFIG_IMX91_EVK_LPDDR4) += lpddr4x_timing.o lpddr4x_timing_1g_JSC.o lpddr4x_timing_2g_JSC.o
endif
endif
