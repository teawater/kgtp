KGTP http://teawater.github.io/kgtp/
====
*[Chinese](http://teawater.github.io/kgtp/indexcn.html)*<br>

<pre><code>
#kgtp.py将在本机上自动配置和启动KGTP和GDB。
#第一次使用这个脚本需要等一段时间因为有一些包需要下载。
wget https://raw.githubusercontent.com/teawater/kgtp/master/kgtp.py
sudo python kgtp.py
#访问内核的内存。
(gdb) p jiffies_64
$2 = 5081634360
#在函数vfs_read上设置trace点并收集这个函数的backtrace信息。
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