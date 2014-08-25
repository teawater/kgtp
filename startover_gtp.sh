sudo rmmod gtp
make clean
make D=1
sudo insmod gtp.ko
