
;DEBUG       equ     1
RASTER      equ     1
SOUND       equ     1
USE_NF      equ     1
NO_BREAK    equ     0



dbgRaster   MACRO
    ifne DEBUG
    ifne RASTER
    move.w  \1,$ffff8240.w
    endif
    endif
    ENDM

dbgColor   MACRO
    ifne DEBUG
    move.w  \1,debug_color
    endif
    ENDM

dbgBreak    MACRO
    ifne USE_NF
    ifeq    NO_BREAK
    tst.w   nf_available
    beq.s   .\@
    ; Nat feat break
    move.l  d0,-(sp)
    move.l  nfid_debugger,-(sp)
    subq.w  #4,sp
    dc.w    $7301
    addq.w  #8,sp
    move.l  (sp)+,d0
.\@:

    endif
    endif
    ENDM

dbgDefStr  MACRO
    ifne USE_NF
\1: dc.b    \2,10,13,0
    endif
    ENDM

    section text

debug_init:
	bsr.s init_natfeats

 	rts

;-----------------------------------
; check if natfeats are available...
;-----------------------------------

    ifne    USE_NF
init_natfeats:
    ; Note: this will probably break on Coldfire

    ; save old illegal instruction vector
    move.l  $10.w,-(sp)
    move.l  #nat_fail,$10.w
    move.l  sp,a4

    move.l  #-1,d0
    pea     nf_version_str
    move.l  #0,-(sp)
    dc.w    $7300
    addq.w  #8,sp

    ; restore illegal instruction vector
    move.l  (sp)+,$10.w
    move.w  #1,nf_available

.continue

    pea     nf_stderr_str
    subq.w  #4,sp
    dc.w    $7300
    addq.w  #8,sp
    move.l  d0,nfid_stderr

    pea     nf_debugger_str
    subq.w  #4,sp
    dc.w    $7300
    addq.w  #8,sp
    move.l  d0,nfid_debugger


    pea     mah_debugstring
    move.l  nfid_stderr,-(sp)
    subq.w  #4,sp
    dc.w    $7301
    lea     12(sp),sp
    rts

nat_fail:
    move.l  a4,sp   ; restore old stack
    move.l  (sp)+,$10.w
    move.w  #0,nf_available
    rts

    section data

nf_version_str      dc.b    "NF_VERSION",0
nf_debugger_str     dc.b    "NF_DEBUGGER",0
nf_stderr_str       dc.b    "NF_STDERR",0
mah_debugstring     dc.b    "This is my debug string",10,13,"don't know if it works",10,13,0
    even

nf_available    dc.w    0

nfid_stderr     dc.l    0
nfid_debugger   dc.l    0

    endif


