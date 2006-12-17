# TODO
# - use system perl packages
# - CC & CFLAGS
# - use system whois (same sources)
#
%include	/usr/lib/rpm/macros.perl
Summary:	Psad analyzes iptables log messages for suspect traffic
Name:		psad
Version:	2.0.1
Release:	0.4
License:	GPL
Group:		Daemons
URL:		http://www.cipherdyne.org/psad/
Source0:	http://www.cipherdyne.org/psad/download/%{name}-%{version}.tar.gz
# Source0-md5:	a1604b68e31178e7e0cbbfd7c1cd4edf
BuildRequires:	perl-base
BuildRequires:	rpm-perlprov >= 4.1-13
BuildRequires:	rpmbuild(macros) >= 1.268
Requires(post,preun):	/sbin/chkconfig
Requires:	rc-scripts
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

install -d $RPM_BUILD_ROOT/var/{log,lib,run}/psad

### whois_psad binary
install -d $RPM_BUILD_ROOT%{_bindir}
install -d $RPM_BUILD_ROOT%{_mandir}/man8
install -d $RPM_BUILD_ROOT%{_mandir}/man1
install -d $RPM_BUILD_ROOT%{_sbindir}
### psad config
install -d $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
### psad init script
install -d $RPM_BUILD_ROOT/etc/rc.d/init.d

install {psad,kmsgsd,psadwatchd} $RPM_BUILD_ROOT%{_sbindir}
install fwcheck_psad.pl $RPM_BUILD_ROOT%{_sbindir}/fwcheck_psad
install whois/whois $RPM_BUILD_ROOT%{_bindir}/whois_psad
install nf2csv $RPM_BUILD_ROOT%{_bindir}/nf2csv
install init-scripts/psad-init.redhat $RPM_BUILD_ROOT/etc/rc.d/init.d/psad
install {psad.conf,kmsgsd.conf,psadwatchd.conf,fw_search.conf,alert.conf} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install {signatures,icmp_types,ip_options,auto_dl,snort_rule_dl,posf,pf.os} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install *.8 $RPM_BUILD_ROOT%{_mandir}/man8/
install nf2csv.1 $RPM_BUILD_ROOT%{_mandir}/man1

### install snort rules files
cp -a snort_rules $RPM_BUILD_ROOT%{_sysconfdir}/%{name}

touch $RPM_BUILD_ROOT/var/lib/psad/psadfifo

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ "$1" = 1 ]; then
	hostname=`hostname 2>&1`
	if [ "$hostname" ]; then
		%{__sed} -i -e "s/^HOSTNAME.*;/HOSTNAME	$hostname;/" %{_sysconfdir}/%{name}/{psadwatchd.conf,psad.conf}
	fi

# TODO: files
	touch /var/log/psad/fwdata
	chown root:root /var/log/psad/fwdata
	chmod 600 /var/log/psad/fwdata
	if [ ! -p /var/lib/psad/psadfifo ]; then
		[ -e /var/lib/psad/psadfifo ] && rm -f /var/lib/psad/psadfifo
		mknod -m 600 /var/lib/psad/psadfifo p
	fi
	chown root:root /var/lib/psad/psadfifo
	chmod 0600 /var/lib/psad/psadfifo

%banner -e %{name} <<EOF
[+] You should add to syslog.conf:
    kern.info	| /var/lib/psad/psadfifo

[+] You can edit the EMAIL_ADDRESSES variable in %{_sysconfdir}/psad/psad.conf
 %{_sysconfdir}/psad/psadwatchd.conf to have email alerts sent to an address
    other than root@localhost

[+] Be sure to edit the HOME_NET variable in %{_sysconfdir}/psad/psad.conf
    to define the internal network(s) attached to your machine.

EOF
fi

/sbin/chkconfig --add psad
%service psad restart

%preun
if [ "$1" = 0 ]; then
	%service psad stop
	/sbin/chkconfig --del psad
fi

%files
%defattr(644,root,root,755)
%dir %{_sysconfdir}/%{name}
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/*.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/signatures
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/auto_dl
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/ip_options
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/snort_rule_dl
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/posf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/pf.os
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/icmp_types

%dir %{_sysconfdir}/%{name}/snort_rules
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/snort_rules/*

%attr(754,root,root) /etc/rc.d/init.d/psad
%attr(755,root,root) %{_sbindir}/*
%attr(755,root,root) %{_bindir}/*
%{_mandir}/man8/*
%{_mandir}/man1/*

%dir /var/log/psad
%dir /var/lib/psad
%ghost /var/lib/psad/psadfifo
%dir /var/run/psad

# perl files
%{_mandir}/man3/IPTables::ChainMgr.3pm*
%{_mandir}/man3/IPTables::Parse.3pm*
%{_mandir}/man3/Psad.3pm*
%{perl_vendorlib}/IPTables/ChainMgr.pm
%{perl_vendorlib}/IPTables/Parse.pm
%{perl_vendorlib}/Psad.pm
