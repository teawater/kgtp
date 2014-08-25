sudo gdb /usr/lib/debug/lib/modules/3.14.8-200.fc20.x86_64/vmlinux -ex 'target remote /sys/kernel/debug/gtp' -ex 'set remote trace-buffer-size on'
