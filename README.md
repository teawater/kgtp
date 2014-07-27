 [KGTP](http://teawater.github.io/kgtp/)
====

#### What is KGTP?

KGTP is a comprehensive dynamic tracer for analysing Linux kernel and application (including Android) problems on production systems in real time.

To use it, you don't need patch or rebuild the Linux kernel. Just build KGTP module and insmod it is OK. 

It makes Linux Kernel supply a GDB remote debug interface. Then GDB in current machine or remote machine can debug and trace Linux kernel and user space program through GDB tracepoint and some other functions without stopping the Linux Kernel.
And even if the board doesn't have GDB on it and doesn't have interface for remote debug. It can debug the Linux Kernel using offline debug (See /sys/kernel/debug/gtpframe and offline debug).

KGTP supports X86-32, X86-64, MIPS and ARM.

KGTP supports most versions of the kernel (from 2.6.18 to upstream).

http://www.youtube.com/watch?v=7nfGAbNsEZY or http://www.tudou.com/programs/view/fPu_koiKo38/ is the video that introduced KGTP in English.

http://www.infoq.com/cn/presentations/gdb-sharp-knife-kgtp-linux-kernel is the video that introduced KGTP in Chinese.

Refer more details about `KGTP` in *Chinese* [here](http://teawater.github.io/kgtp/indexcn.html).

#### How to use KGTP?

Refer to the source code blow.

``` python
#kgtp.py will auto setup and start KGTP and GDB in current machine.
#The first time you use this script needs to wait for a while because there are some packages to download.
wget https://raw.githubusercontent.com/teawater/kgtp/master/kgtp.py
sudo python kgtp.py
#Access memory of Linux kernel.
(gdb) p jiffies_64
$2 = 5081634360
#Set tracepoint in function vfs_read to collect its backtrace.
(gdb) trace vfs_read
Tracepoint 1 at 0xffffffff811b8c70: file fs/read_write.c, line 382.
(gdb) actions 
Enter actions for tracepoint 1, one per line.
End with a line saying just "end".
>collect $bt
>end
(gdb) tstart 
(gdb) tstop 
(gdb) tfind 
Found trace frame 0, tracepoint 1
#0 vfs_read (file=file@entry=0xffff88022017b000, 
 buf=buf@entry=0x7fff0fdd80f0 <Address 0x7fff0fdd80f0 out of bounds>, 
 count=count@entry=16, pos=pos@entry=0xffff8800626aff50) at fs/read_write.c:382
382 {
(gdb) bt
#0 vfs_read (file=file@entry=0xffff88022017b000, 
 buf=buf@entry=0x7fff0fdd80f0 <Address 0x7fff0fdd80f0 out of bounds>, 
 count=count@entry=16, pos=pos@entry=0xffff8800626aff50) at fs/read_write.c:382
#1 0xffffffff811b9819 in SYSC_read (count=16, 
 buf=0x7fff0fdd80f0 <Address 0x7fff0fdd80f0 out of bounds>, fd=<optimized out>)
 at fs/read_write.c:506
```
