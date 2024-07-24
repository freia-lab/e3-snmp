where_am_I := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
include $(E3_REQUIRE_TOOLS)/driver.makefile



EXCLUDE_ARCHS = linux-ppc64e6500
EXCLUDE_ARCHS += linux-corei7-poky

APP:=snmpApp
APPDB:=$(APP)/Db
APPSRC:=$(APP)/src
NVENTSUP:=NventSGP/nventSgpSup

USR_CFLAGS   += $(shell net-snmp-config --cflags)
USR_CFLAGS   += -DNETSNMP_NO_INLINE

USR_LDFLAGS  += -Wl,--no-as-needed
USR_LDFLAGS  += $(shell net-snmp-config --libs)

USR_CFLAGS   += $(shell $(PERL) $(where_am_I)$(APPSRC)/getNetSNMPversion.pl)
USR_CPPFLAGS += $(shell $(PERL) $(where_am_I)$(APPSRC)/getNetSNMPversion.pl)

TEMPLATES += $(wildcard $(APPDB)/*.db)
TEMPLATES += $(wildcard $(APPDB)/*.template)
TEMPLATES += $(wildcard $(NVENTSUP)/*.db)

SOURCES   += $(APPSRC)/snmpRegister.cpp
SOURCES   += $(APPSRC)/snmpSessShow.c
SOURCES   += $(APPSRC)/devSnmp.cpp

DBDS      += $(APPSRC)/devSnmp.dbd

SCRIPTS += $(wildcard ../mibs/*-MIB)
SCRIPTS += $(wildcard NventSGP/mibs/*-MIB.txt)

USR_DBFLAGS += -I . -I ..
USR_DBFLAGS += -I $(EPICS_BASE)/db
USR_DBFLAGS += -I $(APPDB)

SUBS=$(wildcard $(APPDB)/*.substitutions)

.PHONY: vlibs
vlibs:
