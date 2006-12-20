# TODO
# - use system snort rules?
%include	/usr/lib/rpm/macros.perl
Summary:	Analyze iptables log messages for suspect traffic
Summary(pl):	Narzêdzie do analizy logów iptables pod k±tem podejrzanego ruchu
Name:		psad
Version:	2.0.1
Release:	0.11
License:	GPL
Group:		Networking/Daemons
Source0:	http://www.cipherdyne.org/psad/download/%{name}-%{version}.tar.gz
# Source0-md5:	a1604b68e31178e7e0cbbfd7c1cd4edf
Source1:	%{name}.init
Patch0:		%{name}-make.patch
Patch1:		%{name}-whois.patch
Patch2:		%{name}-no-wheel.patch
URL:		http://www.cipherdyne.org/psad/
BuildRequires:	perl-base
BuildRequires:	rpm-perlprov >= 4.1-13
BuildRequires:	rpmbuild(macros) >= 1.268
%if %{with autodeps}
BuildRequires:	perl-Bit-Vector
BuildRequires:	perl-Date-Calc
BuildRequires:	perl-IPTables-ChainMgr
BuildRequires:	perl-IPTables-Parse
BuildRequires:	perl-Net-IPv4Addr
BuildRequires:	perl-Unix-Syslog
%endif
Requires(post,preun):	/sbin/chkconfig
Requires:	rc-scripts
Requires:	iptables
Requires:	perl-Date-Calc
Requires:	perl-IPTables-ChainMgr
Requires:	perl-IPTables-Parse
Requires:	whois
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Port Scan Attack Detector (psad) is a collection of three lightweight
system daemons (two main daemons and one helper daemon) that run on
Linux machines and analyze Netfilter log messages to detect port scans
and other suspicious traffic.

%description -l pl
Port Scan Attack Detector (psad) to zbiór trzech lekkich demonów
systemowych (dwóch g³ównych i jednego pomocniczego) dzia³aj±cych na
maszynach linuksowych i analizuj±cych logi Netfiltra, aby wykryæ
skanowanie portów i inny podejrzany ruch.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1

rm -rf Bit-Vector
rm -rf Date-Calc
rm -rf Net-IPv4Addr
rm -rf Unix-Syslog
rm -rf IPTables-Parse
rm -rf IPTables-ChainMgr
rm -rf whois

%build
cd Psad
%{__perl} Makefile.PL \
	INSTALLDIRS=vendor
cd ..

### build psad binaries (kmsgsd and psadwatchd)
%{__make} \
	OPTS="%{rpmcflags}"

### build perl modules used by psad
%{__make} -C Psad \
	OPTIMIZE="%{rpmcflags}"

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{/var/{log,lib,run}/psad,%{_sbindir},%{_bindir},/etc/rc.d/init.d,%{_sysconfdir}/%{name},%{_mandir}/man{1,8}}

%{__make} -C Psad \
	pure_install \
	DESTDIR=$RPM_BUILD_ROOT
rm -f $RPM_BUILD_ROOT%{perl_vendorarch}/auto/Psad/.packlist

install {psad,kmsgsd,psadwatchd} $RPM_BUILD_ROOT%{_sbindir}
install fwcheck_psad.pl $RPM_BUILD_ROOT%{_sbindir}/fwcheck_psad
install nf2csv $RPM_BUILD_ROOT%{_bindir}/nf2csv
install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/psad
install {psad.conf,kmsgsd.conf,psadwatchd.conf,fw_search.conf,alert.conf} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install {signatures,icmp_types,ip_options,auto_dl,snort_rule_dl,posf,pf.os} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}
install *.8 $RPM_BUILD_ROOT%{_mandir}/man8
install nf2csv.1 $RPM_BUILD_ROOT%{_mandir}/man1

### install snort rules files
cp -a snort_rules $RPM_BUILD_ROOT%{_sysconfdir}/%{name}

touch $RPM_BUILD_ROOT/var/lib/psad/psadfifo

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ "$1" = "1" ]; then
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

[+] You can edit the EMAIL_ADDRESSES variable in %{_sysconfdir}/psad/psad.conf and
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
%attr(755,root,root) %{_bindir}/nf2csv
%attr(755,root,root) %{_sbindir}/fwcheck_psad
%attr(755,root,root) %{_sbindir}/kmsgsd
%attr(755,root,root) %{_sbindir}/psad
%attr(755,root,root) %{_sbindir}/psadwatchd
%{_mandir}/man1/nf2csv.1*
%{_mandir}/man8/kmsgsd.8*
%{_mandir}/man8/psad.8*
%{_mandir}/man8/psadwatchd.8*

%dir /var/log/psad
%dir /var/lib/psad
%ghost /var/lib/psad/psadfifo
%dir /var/run/psad

# perl files
%{_mandir}/man3/Psad.3pm*
%{perl_vendorlib}/Psad.pm
