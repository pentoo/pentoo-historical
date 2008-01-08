#/bin/sh!

# Purge the uneeded locale, should keeps only en
localepurge

# Runs the incredible menu generator
genmenu.py -v
env-update && source /etc/profile

# Fix the root login by emptying the root password. No ssh will be allowed until 'passwd root'
sed -i -e 's/^root:\*:/root::/' /etc/shadow

# compile mingw32
crossdev i686-mingw32

#clean out kernel and make prepare for future modules support
cd /usr/src/linux
mv .config ../
make clean
make mrproper
mv ../.config ./
make prepare

cd /opt/
mkdir exploits/packetstorm -p
for file in `ls *.tgz`
do
	tar -zxf ${file} -C exploits/packetstorm/
	rm -f ${file}
done
tar -jxf milw0rm.tar.bz2 -C exploits/
rm -f milw0rm.tar.bz2
