
AS = $(PREFIX)vasmm68k_mot
#AS = $(PREFIX)vasm
UPX = $(shell which upx)
#UPX =
AS_FLAGS = -m68000 -devpac

LD = $(PREFIX)vlink
LD_FLAGS = -bataritos -d -s

BUILDDIR = build/

DATA = sintab.bin ball.bin vulk.bin ball.plt

#ifeq ($(MAKECMDGOALS),synced)
OUT = ffs.prg
SRC = f.s
DEPS = setup.s debug.s
#endif

.PHONY: all test sttest stetest release clean

all: $(BUILDDIR) $(OUT)


$(OUT): $(DATA) $(SRC) $(DEPS)
	$(AS) $(AS_FLAGS) -Ftos -o $(OUT) $(SRC)

# DATA

sintab.bin:
	python sine.py

ball.bin:
	python gfxext.py data.def

# test targets

test: sttest

sttest: all
	python test.py -m st $(OUT)

stetest: all
	python test.py -m ste $(OUT)

debug: all
	python test.py -m ste --debug  $(OUT)

gfxext.py: data.def

release: $(OUT)
ifneq ($(strip $(UPX)),)
	$(UPX) --small --small $(OUT)
else
	@echo "UPX not found"
endif
	zip ffsvulk.zip ffs.prg readme.txt

clean:
	rm -f $(addprefix $(BUILDDIR),$(OBJS)) $(OUT) $(DATA)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)
