%define psadlibdir %{_libdir}/%{name}
%define psadlogdir /var/log/psad
%define psadrundir /var/run/psad
%define psadvarlibdir /var/lib/psad

### get the first @INC directory that includes the string "linux".
### This may be 'i386-linux', or 'i686-linux-thread-multi', etc.
%define psadmoddir `perl -e '$path='i386-linux'; for (@INC) { if($_ =~ m|.*/(.*linux.*)|) {$path = $1; last; }} print $path'`

Summary:	Psad analyzes iptables log messages for suspect traffic
Name:		psad
Version:	2.0.1
Release:	0.1
License:	GPL
Group:		Daemons
URL:		http://www.cipherdyne.org/psad/
Source0:	http://www.cipherdyne.org/psad/download/%{name}-%{version}.tar.gz
# Source0-md5:	a1604b68e31178e7e0cbbfd7c1cd4edf
BuildRequires:	perl-base
Requires:	iptables
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Port Scan Attack Detector (psad) is a collection of three lightweight
system daemons written in Perl and in C that are designed to work with
Linux iptables firewalling code to detect port scans and other suspect
traffic. It features a set of highly configurable danger thresholds
(with sensible defaults provided), verbose alert messages that include
the source, destination, scanned port range, begin and end times, tcp
flags and corresponding nmap options, reverse DNS info, email and
syslog alerting, automatic blocking of offending ip addresses via
dynamic configuration of iptables rulesets, and passive operating
system fingerprinting. In addition, psad incorporates many of the tcp,
udp, and icmp signatures included in the snort intrusion detection
system (http://www.snort.org) to detect highly suspect scans for
various backdoor programs (e.g. EvilFTP, GirlFriend, SubSeven), DDoS
tools (mstream, shaft), and advanced port scans (syn, fin, xmas) which
are easily leveraged against a machine via nmap. psad can also alert
on snort signatures that are logged via fwsnort
(http://www.cipherdyne.org/fwsnort/), which makes use of the iptables
string match module to detect application layer signatures.


%prep
%setup -q

for i in $(grep -r "use lib" . | cut -d: -f1); do
awk '/use lib/ { sub("%{_prefix}/lib/psad", "%{_libdir}/%{name}") } { print }' $i > $i.tmp
	mv $i.tmp $i
done

# FIXME - do it with a loop
perl Psad/Makefile.PL PREFIX=%{psadlibdir} LIB=%{psadlibdir}
perl IPTables-Parse/Makefile.PL PREFIX=%{psadlibdir} LIB=%{psadlibdir}
perl IPTables-ChainMgr/Makefile.PL PREFIX=%{psadlibdir} LIB=%{psadlibdir}
perl Bit-Vector/Makefile.PL PREFIX=%{psadlibdir} LIB=%{psadlibdir}
perl Net-IPv4Addr/Makefile.PL PREFIX=%{psadlibdir} LIB=%{psadlibdir}
perl Unix-Syslog/Makefile.PL PREFIX=%{psadlibdir} LIB=%{psadlibdir}
perl Date-Calc/Makefile.PL PREFIX=%{psadlibdir} LIB=%{psadlibdir}

%build
### build psad binaries (kmsgsd and psadwatchd)
%{__make} OPTS="$RPM_OPT_FLAGS"

### build the whois client
%{__make} OPTS="$RPM_OPT_FLAGS" -C whois

### build perl modules used by psad
%{__make} OPTS="$RPM_OPT_FLAGS" -C Psad
%{__make} OPTS="$RPM_OPT_FLAGS" -C IPTables-Parse
%{__make} OPTS="$RPM_OPT_FLAGS" -C IPTables-ChainMgr
%{__make} OPTS="$RPM_OPT_FLAGS" -C Bit-Vector
%{__make} OPTS="$RPM_OPT_FLAGS" -C Net-IPv4Addr
%{__make} OPTS="$RPM_OPT_FLAGS" -C Unix-Syslog
%{__make} OPTS="$RPM_OPT_FLAGS" -C Date-Calc

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

### psad module dirs
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Bit/Vector
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Bit
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Psad
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Unix/Syslog
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Date/Calc
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Net/IPv4Addr
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/IPTables/Parse
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/IPTables/ChainMgr
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Unix
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Carp
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calc
install -d $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calendar
install -d $RPM_BUILD_ROOT%{psadlibdir}/auto/Net/IPv4Addr
install -d $RPM_BUILD_ROOT%{psadlibdir}/Net
install -d $RPM_BUILD_ROOT%{psadlibdir}/IPTables

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
install {psad,kmsgsd,psadwatchd} $RPM_BUILD_ROOT%{_sbindir}/
install fwcheck_psad.pl $RPM_BUILD_ROOT%{_sbindir}/fwcheck_psad
install whois/whois $RPM_BUILD_ROOT%{_bindir}/whois_psad
install nf2csv $RPM_BUILD_ROOT%{_bindir}/nf2csv
install init-scripts/psad-init.redhat $RPM_BUILD_ROOT/etc/rc.d/init.d/psad
install {psad.conf,kmsgsd.conf,psadwatchd.conf,fw_search.conf,alert.conf} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/
install {signatures,icmp_types,ip_options,auto_dl,snort_rule_dl,posf,pf.os} $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/
install *.8 $RPM_BUILD_ROOT%{_mandir}/man8/
install nf2csv.1 $RPM_BUILD_ROOT%{_mandir}/man1/

### install perl modules used by psad
install Bit-Vector/blib/arch/auto/Bit/Vector/Vector.so $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Bit/Vector/Vector.so
install Bit-Vector/blib/arch/auto/Bit/Vector/Vector.bs $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Bit/Vector/Vector.bs
install Bit-Vector/blib/lib/Bit/Vector.pm $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Bit/Vector.pm
install Unix-Syslog/blib/arch/auto/Unix/Syslog/Syslog.so $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Unix/Syslog/Syslog.so
install Unix-Syslog/blib/arch/auto/Unix/Syslog/Syslog.bs $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Unix/Syslog/Syslog.bs
install Unix-Syslog/blib/lib/auto/Unix/Syslog/autosplit.ix $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Unix/Syslog/autosplit.ix
install Unix-Syslog/blib/lib/Unix/Syslog.pm $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Unix/Syslog.pm
install Date-Calc/blib/arch/auto/Date/Calc/Calc.so $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Date/Calc/Calc.so
install Date-Calc/blib/arch/auto/Date/Calc/Calc.bs $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/auto/Date/Calc/Calc.bs
install Date-Calc/blib/lib/Carp/Clan.pod $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Carp/Clan.pod
install Date-Calc/blib/lib/Carp/Clan.pm $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Carp/Clan.pm
install Date-Calc/blib/lib/Date/Calc.pm $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calc.pm
install Date-Calc/blib/lib/Date/Calc.pod $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calc.pod
install Date-Calc/blib/lib/Date/Calendar.pm $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calendar.pm
install Date-Calc/blib/lib/Date/Calendar.pod $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calendar.pod
install Date-Calc/blib/lib/Date/Calc/Object.pm $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calc/Object.pm
install Date-Calc/blib/lib/Date/Calc/Object.pod $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calc/Object.pod
install Date-Calc/blib/lib/Date/Calendar/Year.pm $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calendar/Year.pm
install Date-Calc/blib/lib/Date/Calendar/Profiles.pod $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calendar/Profiles.pod
install Date-Calc/blib/lib/Date/Calendar/Profiles.pm $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calendar/Profiles.pm
install Date-Calc/blib/lib/Date/Calendar/Year.pod $RPM_BUILD_ROOT%{psadlibdir}/%{psadmoddir}/Date/Calendar/Year.pod
install Net-IPv4Addr/blib/lib/auto/Net/IPv4Addr/autosplit.ix $RPM_BUILD_ROOT%{psadlibdir}/auto/Net/IPv4Addr/autosplit.ix
install Net-IPv4Addr/blib/lib/Net/IPv4Addr.pm $RPM_BUILD_ROOT%{psadlibdir}/Net/IPv4Addr.pm
install IPTables-Parse/blib/lib/IPTables/Parse.pm $RPM_BUILD_ROOT%{psadlibdir}/IPTables/Parse.pm
install IPTables-ChainMgr/blib/lib/IPTables/ChainMgr.pm $RPM_BUILD_ROOT%{psadlibdir}/IPTables/ChainMgr.pm
install Psad/blib/lib/Psad.pm $RPM_BUILD_ROOT%{psadlibdir}/Psad.pm

### install snort rules files
cp -r snort_rules $RPM_BUILD_ROOT%{_sysconfdir}/%{name}

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

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
chmod 0500 %{_sbindir}/psad
chmod 0500 %{_sbindir}/kmsgsd
chmod 0500 %{_sbindir}/psadwatchd
chmod 0600 %{psadlogdir}/fwdata
if [ ! -p %psadvarlibdir/psadfifo ];
then [ -e %psadvarlibdir/psadfifo ] && /bin/rm -f %psadvarlibdir/psadfifo
/bin/mknod -m 600 %psadvarlibdir/psadfifo p
fi
chown root.root %psadvarlibdir/psadfifo
chmod 0600 %psadvarlibdir/psadfifo
### make psad start at boot
/sbin/chkconfig --add psad
if [ -f %{_sysconfdir}/syslog.conf ];
then [ -f %{_sysconfdir}/syslog.conf.orig ] || cp -p %{_sysconfdir}/syslog.conf %{_sysconfdir}/syslog.conf.orig
### add the psadfifo line to %{_sysconfdir}/syslog.conf if necessary
if ! grep -v "#" %{_sysconfdir}/syslog.conf | grep -q psadfifo;
then echo "[+] Adding psadfifo line to %{_sysconfdir}/syslog.conf"
echo "kern.info |/var/lib/psad/psadfifo" >> %{_sysconfdir}/syslog.conf
    fi
    if [ -e /var/run/syslogd.pid ];
    then
    echo "[+] Restarting syslogd "
    kill -HUP `cat /var/run/syslogd.pid`
    fi
fi
if grep -q "EMAIL.*root.*localhost" %{_sysconfdir}/psad/psad.conf;
then
echo "[+] You can edit the EMAIL_ADDRESSES variable in %{_sysconfdir}/psad/psad.conf"
echo " %{_sysconfdir}/psad/psadwatchd.conf to have email alerts sent to an address"
echo "    other than root\@localhost"
fi

if grep -q "HOME_NET.*CHANGEME" %{_sysconfdir}/psad/psad.conf;
then
echo "[+] Be sure to edit the HOME_NET variable in %{_sysconfdir}/psad/psad.conf"
echo "    to define the internal network(s) attached to your machine."
fi

%preun
#%_preun_service psad

%files
%defattr(644,root,root,755)
%dir %{psadlogdir}
%dir %psadvarlibdir
%dir %psadrundir
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

%{_libdir}/%{name}
