# TODO
# - use system perl packages
# - CC & CFLAGS
# - use system whois (same sources)
#
%define psadlibdir %{_libdir}/%{name}
%define psadlogdir /var/log/psad
%define psadrundir /var/run/psad
%define psadvarlibdir /var/lib/psad

### get the first @INC directory that includes the string "linux".
### This may be 'i386-linux', or 'i686-linux-thread-multi', etc.
# TODO: kill this
%define psadmoddir `perl -e '$path='i386-linux'; for (@INC) { if($_ =~ m|.*/(.*linux.*)|) {$path = $1; last; }} print $path'`

%include	/usr/lib/rpm/macros.perl
Summary:	Psad analyzes iptables log messages for suspect traffic
Name:		psad
Version:	2.0.1
Release:	0.3
License:	GPL
Group:		Daemons
URL:		http://www.cipherdyne.org/psad/
Source0:	http://www.cipherdyne.org/psad/download/%{name}-%{version}.tar.gz
# Source0-md5:	a1604b68e31178e7e0cbbfd7c1cd4edf
BuildRequires:	perl-base
BuildRequires:	rpm-perlprov >= 4.1-13
%if %{with autodeps}
BuildRequires:	perl-Bit-Vector
BuildRequires:	perl-Date-Calc
BuildRequires:	perl-Net-IPv4Addr
BuildRequires:	perl-Unix-Syslog
%endif
Requires:	iptables
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Port Scan Attack Detector (psad) is a collection of three lightweight
system daemons (two main daemons and one helper daemon) that run on
Linux machines and analyze Netfilter log messages to detect port scans
and other suspicious traffic.

%prep
%setup -q
rm -rf Bit-Vector
rm -rf Date-Calc
rm -rf Net-IPv4Addr
rm -rf Unix-Syslog

%build
DIRS="Psad IPTables-Parse IPTables-ChainMgr"
for i in $DIRS; do
	cd $i
	%{__perl} Makefile.PL \
		INSTALLDIRS=vendor
	cd ..
done

### build psad binaries (kmsgsd and psadwatchd)
%{__make} \
	OPTS="%{rpmcflags}"

### build the whois client
%{__make} -C whois \
	OPTS="%{rpmcflags}"

### build perl modules used by psad
%{__make} -C Psad \
	OPTIMIZE="%{rpmcflags}"
%{__make} -C IPTables-Parse \
	OPTIMIZE="%{rpmcflags}"
%{__make} -C IPTables-ChainMgr \
	OPTIMIZE="%{rpmcflags}"

%install
rm -rf $RPM_BUILD_ROOT
### config directory
#install -d $RPM_BUILD_ROOT%{psadetcdir}
### log directory
install -d $RPM_BUILD_ROOT%{psadlogdir}
### dir for psadfifo
install -d $RPM_BUILD_ROOT%{psadvarlibdir}
### dir for pidfiles
install -d $RPM_BUILD_ROOT%{psadrundir}

%{__make} -C Psad \
	pure_install \
	DESTDIR=$RPM_BUILD_ROOT
rm -f $RPM_BUILD_ROOT%{perl_vendorarch}/auto/Psad/.packlist

%{__make} -C IPTables-Parse \
	pure_install \
	DESTDIR=$RPM_BUILD_ROOT
rm -f $RPM_BUILD_ROOT%{perl_vendorarch}/auto/IPTables/Parse/.packlist

%{__make} -C IPTables-ChainMgr \
	pure_install \
	DESTDIR=$RPM_BUILD_ROOT
rm -f $RPM_BUILD_ROOT%{perl_vendorarch}/auto/IPTables/ChainMgr/.packlist


### whois_psad binary
install -d $RPM_BUILD_ROOT%{_bindir}
install -d $RPM_BUILD_ROOT%{_mandir}/man8
install -d $RPM_BUILD_ROOT%{_mandir}/man1
install -d $RPM_BUILD_ROOT%{_sbindir}
### psad config
install -d $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
### psad init script
install -d $RPM_BUILD_ROOT/etc/rc.d/init.d

### the 700 permissions mode is fixed in the
### %post phase
install {psad,kmsgsd,psadwatchd} $RPM_BUILD_ROOT%{_sbindir}
install fwcheck_psad.pl $RPM_BUILD_ROOT%{_sbindir}/fwcheck_psad
install whois/whois $RPM_BUILD_ROOT%{_bindir}/whois_psad
install nf2csv $RPM_BUILD_ROOT%{_bindir}/nf2csv
install init-scripts/psad-init.redhat $RPM_BUILD_ROOT/etc/rc.d/init.d/psad
install {psad.conf,kmsgsd.conf,psadwatchd.conf,fw_search.conf,alert.conf} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install {signatures,icmp_types,ip_options,auto_dl,snort_rule_dl,posf,pf.os} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install *.8 $RPM_BUILD_ROOT%{_mandir}/man8/
install nf2csv.1 $RPM_BUILD_ROOT%{_mandir}/man1/

### install snort rules files
cp -r snort_rules $RPM_BUILD_ROOT%{_sysconfdir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%pre
#if [ ! -p /var/lib/psad/psadfifo ];
#then [ -e /var/lib/psad/psadfifo ] && /bin/rm -f /var/lib/psad/psadfifo
#fi
#/bin/mknod -m 600 /var/lib/psad/psadfifo p
#chown root.root /var/lib/psad/psadfifo
#chmod 0600 /var/lib/psad/psadfifo

%post
### put the current hostname into the psad C binaries
### (kmsgsd and psadwatchd).
perl -p -i -e 'use Sys::Hostname; my $hostname = hostname(); s/HOSTNAME(\s+)_?CHANGE.?ME_?/HOSTNAME${1}$hostname/' %{_sysconfdir}/%{name}/psad.conf
perl -p -i -e 'use Sys::Hostname; my $hostname = hostname(); s/HOSTNAME(\s+)_?CHANGE.?ME_?/HOSTNAME${1}$hostname/' %{_sysconfdir}/%{name}/psadwatchd.conf

/bin/touch %{psadlogdir}/fwdata
chown root.root %{psadlogdir}/fwdata
chmod 0600 %{psadlogdir}/fwdata
if [ ! -p %psadvarlibdir/psadfifo ];
	then [ -e %psadvarlibdir/psadfifo ] && /bin/rm -f %psadvarlibdir/psadfifo
	/bin/mknod -m 600 %psadvarlibdir/psadfifo p
fi
chown root.root %psadvarlibdir/psadfifo
chmod 0600 %psadvarlibdir/psadfifo
### make psad start at boot
/sbin/chkconfig --add psad
if [ -f /etc/syslog.conf ]; then
	[ -f /etc/syslog.conf.orig ] || cp -p /etc/syslog.conf /etc/syslog.conf.orig

	### add the psadfifo line to /etc/syslog.conf if necessary
	if ! grep -v "#" /etc/syslog.conf | grep -q psadfifo; then
		echo "[+] Adding psadfifo line to /etc/syslog.conf"
		echo "kern.info |/var/lib/psad/psadfifo" >> /etc/syslog.conf
	fi
	if [ -e /var/run/syslogd.pid ]; then
		echo "[+] Restarting syslogd "
		kill -HUP `cat /var/run/syslogd.pid`
	fi
fi
if grep -q "EMAIL.*root.*localhost" %{_sysconfdir}/psad/psad.conf; then
	echo "[+] You can edit the EMAIL_ADDRESSES variable in %{_sysconfdir}/psad/psad.conf"
	echo " %{_sysconfdir}/psad/psadwatchd.conf to have email alerts sent to an address"
	echo "    other than root\@localhost"
fi

if grep -q "HOME_NET.*CHANGEME" %{_sysconfdir}/psad/psad.conf; then
	echo "[+] Be sure to edit the HOME_NET variable in %{_sysconfdir}/psad/psad.conf"
	echo "    to define the internal network(s) attached to your machine."
fi

%preun
#%_preun_service psad

%files
%defattr(644,root,root,755)
%dir %{psadlogdir}
%dir %{psadvarlibdir}
%dir %{psadrundir}
%attr(754,root,root) /etc/rc.d/init.d/psad
%attr(755,root,root) %{_sbindir}/*
%attr(755,root,root) %{_bindir}/*
%{_mandir}/man8/*
%{_mandir}/man1/*

%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/*.conf
%config(noreplace) %{_sysconfdir}/%{name}/signatures
%config(noreplace) %{_sysconfdir}/%{name}/auto_dl
%config(noreplace) %{_sysconfdir}/%{name}/ip_options
%config(noreplace) %{_sysconfdir}/%{name}/snort_rule_dl
%config(noreplace) %{_sysconfdir}/%{name}/posf
%config(noreplace) %{_sysconfdir}/%{name}/pf.os
%config(noreplace) %{_sysconfdir}/%{name}/icmp_types

%dir %{_sysconfdir}/%{name}/snort_rules
%config(noreplace) %{_sysconfdir}/%{name}/snort_rules/*

# perl files
%{_mandir}/man3/IPTables::ChainMgr.3pm*
%{_mandir}/man3/IPTables::Parse.3pm*
%{_mandir}/man3/Psad.3pm*
%{perl_vendorlib}/IPTables/ChainMgr.pm
%{perl_vendorlib}/IPTables/Parse.pm
%{perl_vendorlib}/Psad.pm
