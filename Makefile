ifeq ($(P),1)
obj-m := gtp.o plugin_example.o
else
obj-m := gtp.o
endif

MODULEVERSION := 20140510+

KERNELVERSION ?= $(shell uname -r)
KERNELDIR ?= /lib/modules/$(KERNELVERSION)/build/
CROSS_COMPILE ?=
MODULEDIR ?= /lib/modules/$(KERNELVERSION)/lib/
#ARCH ?= i386
#ARCH ?= x86_64
#ARCH ?= mips
#ARCH ?= arm

export CONFIG_DEBUG_INFO=y

PWD  := $(shell pwd)
ifeq ($(D),1)
EXTRA_CFLAGS += -DGTPDEBUG
endif
ifeq ($(AUTO),0)
EXTRA_CFLAGS += -DGTP_NO_AUTO_BUILD
endif
ifeq ($(FRAME_ALLOC_RECORD),1)
EXTRA_CFLAGS += -DFRAME_ALLOC_RECORD
endif
ifeq ($(FRAME_SIMPLE),1)
EXTRA_CFLAGS += -DGTP_FRAME_SIMPLE
endif
ifeq ($(CLOCK_CYCLE),1)
EXTRA_CFLAGS += -DGTP_CLOCK_CYCLE
endif
ifeq ($(USE_PROC),1)
EXTRA_CFLAGS += -DUSE_PROC
endif

DKMS_FILES := Makefile dkms.conf dkms_others_install.sh                  \
	      dkms_others_uninstall.sh gtp.c gtp_rb.c ring_buffer.c      \
	      ring_buffer.h getmod.c getframe.c putgtprsp.c getgtprsp.pl \
	      howto.txt

default: gtp.ko getmod getframe putgtprsp

clean:
	rm -rf getmod
	rm -rf getframe
	rm -rf putgtprsp
	rm -rf *.o
	rm -rf *.ko
	rm -rf .tmp_versions/
	rm -rf Module.symvers

install: module_install others_install

uninstall: module_uninstall others_uninstall

dkms:
	mkdir -p /usr/src/kgtp-$(MODULEVERSION)/
	cp $(DKMS_FILES) /usr/src/kgtp-$(MODULEVERSION)/

module_install: gtp.ko
	mkdir -p $(MODULEDIR)
	cp gtp.ko $(MODULEDIR)
	depmod -a

module_uninstall:
	rm -rf $(MODULEDIR)gtp.ko
	depmod -a

others_install: program_install

others_uninstall: program_uninstall

program_install: getmod getframe putgtprsp
	cp getmod /sbin/
	chmod 700 /sbin/getmod
	cp getframe /sbin/
	chmod 700 /sbin/getframe
	cp putgtprsp /sbin/
	chmod 700 /sbin/putgtprsp
	cp getgtprsp.pl /bin/
	chmod 755 /bin/getgtprsp.pl
	cp getmod.py /bin/
	chmod 644 /bin/getmod.py

program_uninstall:
	rm -rf /sbin/getmod
	rm -rf /sbin/getframe
	rm -rf /sbin/putgtprsp
	rm -rf /bin/getgtprsp.pl

gtp.ko: gtp.c gtp_rb.c ring_buffer.c ring_buffer.h perf_event.c
ifneq ($(ARCH),)
	$(MAKE) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) -C $(KERNELDIR) M=$(PWD) modules
else
	$(MAKE) CROSS_COMPILE=$(CROSS_COMPILE) -C $(KERNELDIR) M=$(PWD) modules
endif

getmod: getmod.c
ifeq ($(D),1)
	$(CROSS_COMPILE)gcc -g -static -o getmod getmod.c
else
	$(CROSS_COMPILE)gcc -O2 -static -o getmod getmod.c
endif

getframe: getframe.c
ifeq ($(D),1)
	$(CROSS_COMPILE)gcc -g -static -o getframe getframe.c
else
	$(CROSS_COMPILE)gcc -O2 -static -o getframe getframe.c
endif

putgtprsp: putgtprsp.c
ifeq ($(D),1)
	$(CROSS_COMPILE)gcc -g -static -o putgtprsp putgtprsp.c
else
	$(CROSS_COMPILE)gcc -O2 -static -o putgtprsp putgtprsp.c
endif

plugin_example.ko: plugin_example.c gtp_plugin.h
ifneq ($(ARCH),)
	$(MAKE) ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE) -C $(KERNELDIR) M=$(PWD) modules
else
	$(MAKE) CROSS_COMPILE=$(CROSS_COMPILE) -C $(KERNELDIR) M=$(PWD) modules
endif
