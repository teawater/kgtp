#!/usr/bin/perl

# This script to get the GDB tracepoint RSP package and save it
# to ./gtpstart and ./gtpstop file.
# GPL
# Copyright(C) KGTP team (https://code.google.com/p/kgtp/), 2010-2013

binmode STDIN, ":raw";
$| = 1;

$status = 0;
$circular = 0;
$var_count = 0;

while (1) {
	sysread STDIN, $c, 1 or next;
	if ($c eq '') {
		next;
	} elsif ($c eq '+' || $c eq '-') {
		$c = '';
	}

	sysread STDIN, $line, 1024 or next;
	print '+';
	$line = $c.$line;

	open(LOG, ">>./log");
	print LOG $line."\n";
	close (LOG);

	if ($status == 0) {
		if ($line eq '$?#3f') {
			print '$S05#b8';
		} elsif ($line eq '$g#67') {
			print '$00000000#80';
		} elsif ($line eq '$k#6b') {
			exit;
		} elsif ($line =~ /^\$m/ || $line =~ /^\$p/) {
			print '$00000000#80';
		} elsif ($line eq '$qTStatus#49') {
			print '$T0;tnotrun:0;tframes:0;tcreated:0;tsize:';
			print '500000;tfree:500000;circular:0;disconn:0#d1';
		} elsif ($line eq '$QTBuffer:circular:1#f9') {
			print '$OK#9a';
			$circular = 1;
		} elsif ($line eq '$QTBuffer:circular:0#f8') {
			print '$OK#9a';
			$circular = 0;
		} elsif ($line eq '$QTStop#4b') {
			print '$OK#9a';
		} elsif ($line =~ /^\$qSupported/) {
			print '$ConditionalTracepoints+;TracepointSource+#1b';
		} elsif ($line eq '$QTinit#59') {
			$status = 1;
			open(STARTFILE, ">./gtpstart");
			print STARTFILE '$QTDisconnected:1#e3'."\n";
			if ($circular) {
				print STARTFILE '$QTBuffer:circular:1#f9';
			} else {
				print STARTFILE '$QTBuffer:circular:0#f8';
			}
		} elsif ($line eq '$qTfV#81') {
			print '$18:0:1:6972715f636f756e74#ca';
		} elsif ($line eq '$qTsV#8e') {
			#Support from GTP_VAR_VERSION_ID(0x1) to GTP_STEP_ID_ID(0x2d)
			if ($var_count == 0) {
				print '$17:0:1:736f66746972715f636f756e74#a6';
			} elsif ($var_count == 1) {
				print '$16:0:1:686172646972715f636f756e74#70';
			} elsif ($var_count == 2) {
				print '$15:0:1:6c6173745f6572726e6f#59';
			} elsif ($var_count == 3) {
				print '$14:0:1:69676e6f72655f6572726f72#38';
			} elsif ($var_count == 4) {
				print '$13:0:1:7874696d655f6e736563#35';
			} elsif ($var_count == 5) {
				print '$12:0:1:7874696d655f736563#99';
			} elsif ($var_count == 6) {
				print '$11:0:1:6b726574#48';
			} elsif ($var_count == 7) {
				print '$10:0:1:705f70655f656e#e5';
			} elsif ($var_count == 8) {
				print '$f:0:1:6370755f6e756d626572#29';
			} elsif ($var_count == 9) {
				print '$e:0:1:73656c665f7472616365#f8';
			} elsif ($var_count == 10) {
				print '$d:0:1:64756d705f737461636b#22';
			} elsif ($var_count == 11) {
				print '$c:0:1:7072696e746b5f666f726d6174#c7';
			} elsif ($var_count == 12) {
				print '$b:8:1:7072696e746b5f6c6576656c#66';
			} elsif ($var_count == 13) {
				print '$a:0:1:7072696e746b5f746d70#54';
			} elsif ($var_count == 14) {
				print '$9:0:1:6774705f72625f646973636172645f706167655f6e756d626572#2d';
			} elsif ($var_count == 15) {
				print '$8:0:1:636f6f6b65645f7264747363#01';
			} elsif ($var_count == 16) {
				print '$7:0:1:7264747363#57';
			} elsif ($var_count == 17) {
				print '$6:0:1:636f6f6b65645f636c6f636b#8d';
			} elsif ($var_count == 18) {
				print '$5:0:1:636c6f636b#e3';
			} elsif ($var_count == 19) {
				print '$4:0:1:63757272656e745f7468726561645f696e666f#21';
			} elsif ($var_count == 20) {
				print '$3:0:1:63757272656e745f7461736b#c9';
			} elsif ($var_count == 21) {
				print '$2:0:1:6370755f6964#f1';
			} elsif ($var_count == 22) {
				print '$1:bfe30fc:1:6774705f76657273696f6e#94';
			} elsif ($var_count == 23) {
				print '$19:0:1:706970655f7472616365#cb';
			} elsif ($var_count == 24) {
				print '$1a:0:1:63757272656e745f7461736b5f706964#03';
			} elsif ($var_count == 25) {
				print '$1d:200:1:6274#d9';
			} elsif ($var_count == 26) {
				print '$1b:0:1:63757272656e745f7461736b5f75736572#6e';
			} elsif ($var_count == 27) {
				print '$1c:0:1:63757272656e74#bb';
			} elsif ($var_count == 28) {
				print '$1f:0:1:64697361626c65#bc';
			} elsif ($var_count == 29) {
				print '$1e:0:1:656e61626c65#7e';
			} elsif ($var_count == 30) {
				print '$18:0:1:6972715f636f756e74#ca';
			} elsif ($var_count == 31) {
				print '$20:0:1:77617463685f737461746963#a2';
			} elsif ($var_count == 32) {
				print '$21:0:1:77617463685f74797065#d1';
			} elsif ($var_count == 33) {
				print '$22:1:1:77617463685f73697a65#02';
			} elsif ($var_count == 34) {
				print '$23:0:1:77617463685f7365745f6964#da';
			} elsif ($var_count == 35) {
				print '$24:0:1:77617463685f7365745f61646472#a6';
			} elsif ($var_count == 36) {
				print '$25:0:1:77617463685f7374617274#38';
			} elsif ($var_count == 37) {
				print '$26:0:1:77617463685f73746f70#01';
			} elsif ($var_count == 38) {
				print '$27:0:1:77617463685f74726163655f6e756d#75';
			} elsif ($var_count == 39) {
				print '$28:0:1:77617463685f74726163655f61646472#79';
			} elsif ($var_count == 40) {
				print '$29:0:1:77617463685f61646472#d0';
			} elsif ($var_count == 41) {
				print '$2a:0:1:77617463685f76616c#c1';
			} elsif ($var_count == 42) {
				print '$2b:0:1:77617463685f636f756e74#cc';
			} elsif ($var_count == 43) {
				print '$2c:0:1:737465705f636f756e74#5d';
			} elsif ($var_count == 44) {
				print '$2d:0:1:737465705f6964#c0';
			} else {
				print '$l#6c';
			}
			$var_count++;
		} else {
			print '$#00';
		}
	}

	if ($status == 1) {
		print '$OK#9a';

		if (length($line) > 0) {
			print STARTFILE "\n".$line;
		}

		if ($line eq '$QTStart#b3') {
			$status = 0;

			close(STARTFILE);

			open(STOPFILE, ">./gtpstop");
			print STOPFILE '$QTStop#4b';
			close(STOPFILE);
		}
	}
}
