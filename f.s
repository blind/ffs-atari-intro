

SCREENS		equ	8

	include "setup.s"

;----------------------------------------------------------
	section text
;----------------------------------------------------------


;----------------------------------------------------------
main:
	move.w	#$2700,sr
	bsr		init

	move.w	#$2300,sr
.loop
	; update color
	move.w	#$123,$ffff8240.w
	bsr	 	calc_colors


	move.w	#$321,$ffff8240.w
	bsr		ballz
	move.w	#$0,$ffff8240.w

.key btst.b	#0,$fffffc00.w
	beq.s	.no_key
	cmp.b	#$1,$fffffc02.w
	beq.s	.done
	bra.s	.key

.no_key
	move.l	vbl_count,d0
.wait_vbl
	cmp.l	vbl_count,d0
	beq.s	.wait_vbl


	bra.s	.loop
.done
	rts


;----------------------------------------------------------
init:
	move.l	screen_mem,a0
	lea		screen_ptrs,a1

	moveq	#SCREENS-1,d0
.l1	move.l	a0,(a1)+
	lea		32000(a0),a0
	dbra.w	d0,.l1

	move.l	bg,d0
	move.l	bg+4,d1

	lea		screen_ptrs,a2

	moveq	#SCREENS-1,d2
.frame
	move.l	(a2)+,a0
	move.w	#4000-1,d3
.l2
	move.l	d0,(a0)+
	move.l	d1,(a0)+
	dbra.w	d3,.l2

	dbra.w	d2,.frame


    bclr    #5,$fffffa09.w      ; disable timer c interrupt
    bclr    #6,$fffffa09.w      ; disable ikbd interrupt

	move.l	#vbl,$70.w

	movem.l	palette,d0-7
	movem.l	d0-7,$ffff8240.w	; palette



	; Shift balls...

	lea	ball,a0
	lea	sprt1_preshift,a1
	lea	sprt1_shift_list,a2


	; copy unshifted to first buffer...
	moveq	#0,d1
	moveq	#24-1,d0	; rows
.row_cpy
	move.l	(a0)+,(a1)+
	move.l	(a0)+,(a1)+
	move.l	(a0)+,(a1)+
	move.l	(a0)+,(a1)+
	move.l	d1,(a1)+	; pad with clear data.
	move.l	d1,(a1)+

	dbra.w	d0,.row_cpy

	; shift shit.
	lea	sprt1_preshift,a1
	lea	sprt1_preshift+16*24,a2
	move.w	#16*24-5,d7
.shift_loop
	moveq	#4-1,d6
.bp_loop

	move.w	(a1),d0			; bp0
	move.w	8(a1),d1		; bp0
	move.w	16(a1),d2		; bp0
	move.w	24(a1),d3		; bp0
	lsr.w	d0
	roxr.w	d1
	roxr.w	d2
	roxr.w	d3
	move.w	d0,(a2)
	move.w	d1,4(a2)
	move.w	d2,8(a2)
	move.w	d3,16(a2)

	addq.w	#2,a1
	addq.w	#2,a2

	dbra.w	d6,.bp_loop

	dbra.w	d7,.shift_loop


	; update color
	bsr.s 	calc_colors

	rts

;----------------------------------------------------------
calc_colors:
	move.l	color_buff_list,a0
	move.w	#$351,d1
	move.w	#200*8-1,d0
.cl1
	move.w	d1,(a0)+
	addi.w	#$881,d1
	dbra.w	d0,.cl1

	rts

;----------------------------------------------------------
vbl:
	movem.l	d0-7/a0-1,-(sp)

	lea	screen_ptrs,a0
	move.l	(a0),d0

	REPT SCREENS-1
	move.l	4(a0),(a0)+
	ENDR
	move.l	d0,(a0)

	lsr.w	#8,d0
	move.l	d0,$ffff8200.w	; screen base
	move.b  #0,$ffff8260.w  ; low res
;	move.b	#2,$ffff820a.w	; 60 hz


	; Setup raster
    move.b  #$0,$fffffa1b.w     ; stop timer b
    bset.b  #0,$fffffa07.w      ; enable timer b interrupts.
    bset.b  #0,$fffffa13.w      ; enable timer b interrupts.

    move.l  #hbl,$120.w
    move.b  #$8,$fffffa1b.w 	; start timer b - event count mode


	lea		color_buff_list,a0
	move.l	(a0),d0
	move.l	4(a0),(a0)
	move.l	d0,4(a0)
	move.l	d0,color_ptr

	move.w	#$0,$ffff8240.w




	movem.l	(sp)+,d0-7/a0-1
	add.l	#1,vbl_count
	rte
;----------------------------------------------------------
hbl:
    ; Set colors 8-16
    movem.l	a0-1,-(sp)
    move.l	color_ptr,a0
    lea		($ffff8240+16).w,a1
    REPT	4
    move.l	(a0)+,(a1)+
    ENDR

    move.l	a0,color_ptr
    movem.l	(sp)+,a0-1


	move.b  #0,$fffffa0f.w  ; clear in-sevice bit
    move.b  #$0,$fffffa1b.w ; stop

    move.b  #1,$fffffa21.w  ; next line
    move.b  #$8,$fffffa1b.w ; start timer b

	rte

;----------------------------------------------------------
ballz:
	lea		ball_pos,a0
	move.w	(a0),d0	; x
	lea		sprt1_shift_list,a1

	
	move.l	0(a1),a1

	move.l	screen_ptrs+4,a0

;	lea		8000(a0),a0		; fake offset...

	; blit loop
	moveq	#24-1,d0
.blit_row
	;todo.. MASK!
	move.l	(a1)+,(a0)+
	move.l	(a1)+,(a0)+
	move.l	(a1)+,(a0)+
	move.l	(a1)+,(a0)+
	move.l	(a1)+,(a0)+
	move.l	(a1)+,(a0)+
	lea		160-24(a0),a0
	dbra.w	d0,.blit_row

	rts

;----------------------------------------------------------
	section data
;----------------------------------------------------------

ball_pos	dc.w	100,100


vbl_count dc.l	0

palette:
	dc.w	$000,$000,$000,$000,$000,$000,$000,$000
	dc.w	$111,$222,$333,$444,$555,$666,$777,$707

bg:	dc.w	%0101010101010101
	dc.w	%0011001100110011
	dc.w	%0000111100001111
	dc.w	%1111111111111111


sintab:	incbin	"sintab.bin"

ball:	incbin	"ball.bin"

color_buff_list
	dc.l	color_data,color_data+8*200


;----------------------------------------------------------
	section bss
;----------------------------------------------------------

sprt1_shift_list:
	ds.l	16

sprt1_preshift:
	ds.w	16*32*16


screen_ptrs
	ds.l	8

color_ptr
	ds.l	1


color_data
	ds.w	8*200*2
