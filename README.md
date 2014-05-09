KGTP http://teawater.github.io/kgtp/
====
<div style="text-align: center;">
<a href="indexcn.html">Chinese</a><br>
</div>
<br>
<table
style="text-align: left; width: 60%; margin-left: auto; margin-right: auto;"
border="1" cellpadding="0" cellspacing="0">
<tbody>
<tr align="center">
<td style="vertical-align: top;">What is KGTP?<br>
</td>
</tr>
<tr>
<td style="vertical-align: top;">KGTP is a comprehensive dynamic
tracer for analysing Linux kernel and application (including Android)
problems on production systems in real time.<br>
To use it, you don't need patch or rebuild the Linux kernel. Just build
KGTP module and insmod it is OK. <br>
<br>
It makes Linux Kernel supply a GDB remote debug interface. Then GDB in
current machine or remote machine can debug and trace Linux kernel and
user space program through GDB tracepoint and some other functions
without stopping the Linux Kernel.<br>
And even if the board doesn't have GDB on it and doesn't have interface
for remote debug. It can debug the Linux Kernel using offline debug
(See <a href="kgtp.html#/sys/kernel/debug/gtpframe and offline debug|outline">/sys/kernel/debug/gtpframe and offline debug</a>).<br>
<br>
KGTP supports X86-32, X86-64, MIPS and ARM.<br>
KGTP supports most versions of the kernel (from 2.6.18 to upstream).<br>
<br>
<a href="http://www.youtube.com/watch?v=7nfGAbNsEZY">http://www.youtube.com/watch?v=7nfGAbNsEZY</a>
or <a href="http://www.tudou.com/programs/view/fPu_koiKo38/">http://www.tudou.com/programs/view/fPu_koiKo38/</a>
is the video that introduced KGTP in English.<br>
<a
href="http://www.infoq.com/cn/presentations/gdb-sharp-knife-kgtp-linux-kernel">http://www.infoq.com/cn/presentations/gdb-sharp-knife-kgtp-linux-kernel</a>
is the video that introduced KGTP in Chinese.<br>
</td>
</tr>
<tr align="center">
<td style="vertical-align: top;"><br>
</td>
</tr>
<tr align="center">
<td style="vertical-align: top;">How to use KGTP?<br>
</td>
</tr>
<tr>
<td style="vertical-align: top;">
<pre><code>
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
</code></pre>
<br>
Please goto <a href="kgtp.html">KGTP (English)</a> or <a href="kgtpcn.html">KGTPCN (Chinese)</a> to get howto use KGTP.<br>
Or download the pdf version:
<a href="https://raw.github.com/teawater/kgtp/master/kgtp.pdf">kgtp.pdf (English)</a> <a href="https://raw.github.com/teawater/kgtp/master/kgtpcn.pdf"> kgtpcn.pdf (Chinese)</a>.
<br>
<br>
Please see
<a href="kgtp.html#__RefHeading__621_1585187435">Table of different between GDB debug normal program and KGTP</a> get the different between GDB debug normal program
and KGTP if you have experience using GDB debug normal program.
</td>
</tr>
<tr align="center">
<td style="vertical-align: top;"><br>
</td>
</tr>
<tr>
<td style="vertical-align: top;">Please go to <a
href="https://github.com/teawater/kgtp/blob/master/UPDATE">https://github.com/teawater/kgtp/blob/master/UPDATE</a>
to get more info about KGTP update.<br>
<a href="http://www.freelists.org/list/kgtp">http://www.freelists.org/list/kgtp</a>
is the maillist of KGTP.<br>
<b>317654748</b> is the QQ group of KGTP.<br>
If KGTP help you, please <a href="https://me.alipay.com/teawater">donate</a> its development. Thanks!<br>
</a></td>
</tr>
</tbody>
</table>
