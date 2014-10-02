# CSTBox framework
#
# Makefile for building the Debian distribution package containing the
# shared material for home automation services.
#
# author = Eric PASCUAL - CSTB (eric.pascual@cstb.fr)

# name of the CSTBox module
MODULE_NAME=ext-home-automation

include $(CSTBOX_DEVEL_HOME)/lib/makefile-dist.mk

copy_files: \
	copy_python_files \
	copy_etc_files


