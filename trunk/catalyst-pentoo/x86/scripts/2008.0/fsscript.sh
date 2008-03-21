#/bin/sh!

# Purge the uneeded locale, should keeps only en
localepurge

if [[ -e /etc/conf.d/clock ]]
then
	sed -i -e 's/#TIMEZONE="Factory"/TIMEZONE="UTC"/' /etc/conf.d/clock
fi

# Runs the incredible menu generator
genmenu.py -v

# Fix the root login by emptying the root password. No ssh will be allowed until 'passwd root'
sed -i -e 's/^root:\*:/root::/' /etc/shadow

# compile mingw32
crossdev i686-mingw32

cd /opt/
mkdir exploits/packetstorm -p
for file in `ls *.tgz`
do
	tar -zxf ${file} -C exploits/packetstorm/
	rm -f ${file}
done
tar -jxf milw0rm.tar.bz2 -C exploits/
rm -f milw0rm.tar.bz2
