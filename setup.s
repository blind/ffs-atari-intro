
;----------------------------------------------------------
;
; Initialization for ST demos. By blind_io
;
;  Project start: 2002-02-03
;  Latest change: 2017-07-21
;
;----------------------------------------------------------

	opt	p=68000


	IFND	SCREENS
SCREENS		equ	2
	ENDIF

	IFND	SCREEN_SIZE
SCREEN_SIZE	equ	32000
	ENDIF

	section text

;----------------------------------------------------------
;
; Return all unused memory to system.
;

_start:
	move.l	4(sp),a5		; address to basepage
	move.l	$0c(a5),d0		; length of text segment
	add.l	$14(a5),d0		; length of data segment
	add.l	$1c(a5),d0		; length of bss segment
	add.l	#$100,d0		; length of basepage
	add.l	#$2000,d0		; length of stackpointer
	move.l	a5,d1			; address to basepage
	add.l	d0,d1			; end of program
	and.l	#-2,d1			; make address even
	move.l	d1,sp			; new stackspace

	move.l	d0,-(sp)		; mshrink()
	move.l	a5,-(sp)		;
	move.w	d0,-(sp)		;
	move.w	#$4a,-(sp)		;
	trap	#1				;
	lea	12(sp),sp			;


	; Allocate memory for SCREENS

	move.l	#SCREENS*SCREEN_SIZE+256,-(sp)
	move.w	#$48,-(sp)
	trap	#1
	addq.l	#6,sp

	tst.l	d0
	beq		quick_exit	; add some error handling here

	add.l	#$ff,d0
	clr.b	d0

	move.l	d0,screen_mem

	; clear screen memory

	movea.l	d0,a0
	move.w	#((SCREEN_SIZE*SCREENS)/16)-1,d0
.clear_loop
	 REPT	4
	 clr.l	(a0)+
	 ENDR
	dbra	d0,.clear_loop

	clr.l	-(sp)					; Enter supervisor mode
	move.w	#$20,-(sp)
	trap	#1
	addq.l	#6,sp
	move.l	d0,old_sp

	lea	old_palette,a0
	movem.l	$ffff8240.w,d0-7
	movem.l	d0-7,(a0)

	move.b	#$12,$fffffc02.w		; disable mouse reporting

	bsr	save_registers

;----------------------------------------------------------
;
; main stuff here
;
	bsr.w	main

;----------------------------------------------------------
;

exit:
	move.b	#$8,$fffffc02.w		; enable mouse reporting

	bsr		restore_registers

	lea		old_palette,a0
	movem.l	(a0)+,d0-7
	movem.l	d0-7,$ffff8240.w

	move.w 	#$2300,sr 			; Restore Interrupt level

	move.l	old_sp,-(sp)
	move.w	#$20,-(sp)
	trap	#1
	addq.l	#6,sp

quick_exit:
	clr.w	-(sp)
	trap	#1

;------------------------------------------------------------
;
; save_registers - save all necessary hardware registers.
;

save_registers:
	move.w	sr,-(sp)
	move.w	#$2700,sr 		; disable interrupts while reading data.
	lea	saved_regs,a0

	; interrupt vectors
	move.l	$68.w,(a0)+
	move.l	$70.w,(a0)+
	move.l	$114.w,(a0)+
	move.l	$118.w,(a0)+
	move.l	$120.w,(a0)+
	move.l	$134.w,(a0)+
	move.l	$484.w,(a0)+

	; video registers

	; video base address
	move.b 	$ffff8201.w,(a0)+
	move.b 	$ffff8203.w,(a0)+
	move.b 	$ffff820d.w,(a0)+	; For STE

	; Res and mode.
	move.b 	$ffff820a.w,(a0)+	
	move.b 	$ffff8260.w,(a0)+	; Resolution

	; STE scroll registers.
	move.b 	$ffff820f.w,(a0)+	; line width reg (words)
	move.b 	$ffff8265.w,(a0)+ 	; horizontal scroll register.

	; MFP registers..

	move.b	$fffffa1f.w,(a0)+
	move.b	$fffffa21.w,(a0)+
	move.b	$fffffa25.w,(a0)+

	move.b	$fffffa17.w,(a0)+
	move.b	$fffffa19.w,(a0)+
	move.b	$fffffa1b.w,(a0)+

	move.b	$fffffa13.w,(a0)+
	move.b	$fffffa15.w,(a0)+

	move.b	$fffffa07.w,(a0)+
	move.b	$fffffa09.w,(a0)+

	move.w 	(sp)+,sr
	rts

;------------------------------------------------------------
;
; restore_registers - restore all necessary hardware registers.
;

restore_registers:
	move.w	sr,-(sp)
	move.w	#$2700,sr 		; disable interrupts while reading data.

	lea	saved_regs,a0
	move.l	(a0)+,$68.w
	move.l	(a0)+,$70.w
	move.l	(a0)+,$114.w
	move.l	(a0)+,$118.w
	move.l	(a0)+,$120.w
	move.l	(a0)+,$134.w
	move.l	(a0)+,$484.w


	; video registers
	move.b 	(a0)+,$ffff8201.w
	move.b 	(a0)+,$ffff8203.w
	move.b 	(a0)+,$ffff820d.w

	; Res and mode.
	move.b 	(a0)+,$ffff820a.w 	; mode	
	move.b 	(a0)+,$ffff8260.w	; Resolution

	; STE scroll registers.
	move.b 	(a0)+,$ffff820f.w	; line width reg (words)
	move.b 	(a0)+,$ffff8265.w 	; horizontal scroll register.

	; MFP registers..
	move.b	(a0)+,$fffffa1f.w
	move.b	(a0)+,$fffffa21.w
	move.b	(a0)+,$fffffa25.w

	move.b	(a0)+,$fffffa17.w
	move.b	(a0)+,$fffffa19.w
	move.b	(a0)+,$fffffa1b.w

	move.b	(a0)+,$fffffa13.w
	move.b	(a0)+,$fffffa15.w

	move.b	(a0)+,$fffffa07.w
	move.b	(a0)+,$fffffa09.w

	move.w 	(sp)+,sr
	rts


;----------------------------------------------------------
	section	data
;----------------------------------------------------------

;----------------------------------------------------------
	section	bss
;----------------------------------------------------------
old_palette		ds.w	16

old_sp			ds.l	1
	even

saved_regs		ds.l	44	; place to save hardware registers.

	even
screen_mem		ds.l	1	; pointer to allocated screen memory
