;
; FFS by Vulkteamet
; 
; All party code. Don't use A6.
;
; blind io^vulkteamet 2017-07-22
;


	opt		d+
SCREENS		equ	8

	include "setup.s"

	include "debug.s"
;----------------------------------------------------------
	section text
;----------------------------------------------------------

main:
	move.w	#$2700,sr
	bsr		init

	move.w	#$2300,sr
.loop
	; update color
;	move.w	#$123,$ffff8240.w
	bsr	 	update_dist


;	move.w	#$321,$ffff8240.w
	bsr		ballz
;	move.w	#$0,$ffff8240.w

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
	move.w	#$2700,sr	; make sure we stop with the interrupts..
	moveq	#0,d0
	bsr		music
	bsr		music+8

	rts

;----------------------------------------------------------

;----------------------------------------------------------
init:
	moveq	#1,d0
	bsr		music

	bsr.w	debug_init
	bsr.w	init_bg
    bclr    #5,$fffffa09.w      ; disable timer c interrupt
    bclr    #6,$fffffa09.w      ; disable ikbd interrupt

	move.l	#vbl,$70.w

	movem.l	palette,d0-7
	movem.l	d0-7,$ffff8240.w	; palette



	; Shift balls...

	lea	ball,a0
	lea	sprt1_preshift+6,a1


	; copy unshifted to first buffer...
	moveq	#0,d1
	moveq	#32-1,d0	; rows
.row_cpy
	move.l	(a0)+,(a1)+
	move.l	(a0)+,(a1)+
	move.l	(a0)+,(a1)+
	move.l	(a0)+,(a1)+
	move.l	d1,(a1)+	; pad with clear data.
	move.l	d1,(a1)+
	addq	#6,a1
	dbra.w	d0,.row_cpy

	; shift shit.
	lea		sprt1_preshift+6,a1
	lea		sprt1_preshift+30*32+6,a2
	move.w	#32*(16-1)-1,d7
.shift_loop
	moveq	#4-1,d6
.bp_loop

	move.w	(a1),d0			; bp0 block 0
	move.w	8(a1),d1		; bp0 block 1
	move.w	16(a1),d2		; bp0 block 2

	lsr.w	d0
	roxr.w	d1
	roxr.w	d2

	move.w	d0,(a2)
	move.w	d1,8(a2)
	move.w	d2,16(a2)

	addq.l	#2,a1
	addq.l	#2,a2

	dbra.w	d6,.bp_loop

	lea		22(a1),a1		; skip to next row (30-8) (24 gfx + 6 mask)
	lea		22(a2),a2

	dbra.w	d7,.shift_loop

	; setup shift ptrs and masks

	lea		sprt1_preshift,a1
	lea		sprt1_shift_list,a3
	moveq	#16-1,d0
.c1
	move.l	a1,(a3)+

	move.l	a1,a2
	; --
	moveq	#32-1,d6
.row_mask
	lea		6(a2),a0
	REPT 3
	move.w	(a0)+,d1
	or.w	(a0)+,d1
	or.w	(a0)+,d1
	or.w	(a0)+,d1
	not.w	d1
	move.w	d1,(a2)+
	ENDR
	lea		24(a2),a2
	dbra.w	d6,.row_mask
	; --

	lea		32*30(a1),a1
	dbra.w	d0,.c1

	; Prepare vulkdata

	; update color
	bsr.s 	calc_colors

	; setup bg dist
	lea		color_dist,a0
	move.l	a0,dist_ptr
	move.l	a0,dist_ptr_use
	lea		400(a0),a0
	move.l	a0,dist_ptr+4
	bsr		update_dist
	rts

;----------------------------------------------------------
init_bg:

	move.l	screen_mem,a0
	lea		screen_ptrs,a1

	moveq	#SCREENS-1,d0
.l1	move.l	a0,(a1)+
	lea		32000(a0),a0
	dbra.w	d0,.l1

	move.l	bg,d0
	move.l	bg+4,d1

	lea		screen_ptrs,a2

;	rts
	; fill with data
	moveq	#SCREENS-1,d2
.frame
	move.l	(a2)+,a0
	move.w	#4000-1,d3
.l2
	move.l	d0,(a0)+
	move.l	d1,(a0)+
	dbra.w	d3,.l2

	dbra.w	d2,.frame
	rts

;----------------------------------------------------------
calc_colors:
	lea		color_data,a0

	lea		vulk,a1
;	move.w	#$351,d1
	move.w	#228-1,d0
.cl1
	move.l	(a1)+,d4
	move.l	(a1)+,d1
	move.l	(a1)+,d2
	move.l	(a1)+,d3

	move.l	d4,(a0)+
	move.l	d1,(a0)+
	move.l	d2,(a0)+
	move.l	d3,(a0)+

	move.l	d4,(a0)+
	move.l	d1,(a0)+
	move.l	d2,(a0)+
	move.l	d3,(a0)+

	dbra.w	d0,.cl1

	rts

;----------------------------------------------------------
vbl:
	movem.l	d0-7/a0-1,-(sp)

	bsr		music+8

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
	bclr.b	#3,$fffffa17.w		; auto end of interrupt
    move.l  #hbl,$120.w
    move.b  #$8,$fffffa1b.w 	; start timer b - event count mode



    ; vulk offset
	lea		color_data,a6

	move.w	vulk_a,d0
	addq	#4,d0
	move.w	d0,vulk_a
	andi.w	#$1ff,d0
	add.w	d0,d0

	lea		sintab,a0
	move.w	(a0,d0.w),d0

	muls.w	#28*2,d0
	swap	d0

	add.w	#28,d0
	lsl.w	#4,d0
	lea		(a6,d0.w),a6

	move.l	dist_ptr_use,a5
	adda.w	(a5)+,a6
    move.l	(a6)+,$ffff8250.w
    move.l	(a6)+,$ffff8254.w
    move.l	(a6)+,$ffff8258.w
    move.l	(a6)+,$ffff825c.w

	move.w	#$0,$ffff8240.w

	movem.l	(sp)+,d0-7/a0-1
	add.l	#1,vbl_count
	rte

;----------------------------------------------------------
hbl:
    move.l	(a6)+,$ffff8250.w
    move.l	(a6)+,$ffff8254.w
    move.l	(a6)+,$ffff8258.w
    move.l	(a6)+,$ffff825c.w
    add.w	(a5)+,a6
;    lea		16(a6),a6

    move.b  #1,$fffffa21.w  ; next line
    move.b  #$8,$fffffa1b.w ; start timer b

	rte

;----------------------------------------------------------
update_dist:
	move.l	dist_ptr+4,a0
	move.w	distStartA,d0
	move.w	distRowDA,d1
	add.w	d1,d1			; *2
	add.w	d0,d0
;	ror.w	#8,d0
	ror.w	#8,d1
	moveq	#0,d5
	lea		sintab,a1
;	dbgBreak
	moveq	#16,d2
	swap	d2
	move.w	#200-1,d4
.l
	move.w	d0,d3
	andi.w	#$1fe,d3
	move.w	(a1,d3.w),d3
	ext.l	d3
	lsl.l	#5,d3
	swap	d3
	move.w	d3,d2	; save from last row for delta
	addi.w	#16,d3
	swap	d2
	sub.w	d2,d3
	andi.w	#$1e,d3
	move.w	d3,(a0)+

	; update angle
	add.w	d1,d0
	addx.w	d5,d0	; d5 contains 0

	dbra.w	d4,.l

	; update for next frame
	move.l	distStartDA,d0
	add.l	d0,distStartA

	move.l	dist_ptr,d0
	move.l	dist_ptr+4,d1
	move.l	d1,dist_ptr
	move.l	d0,dist_ptr+4
	move.l	d1,dist_ptr_use
	rts

distStartA	dc.l	0
distRowDA	dc.l	$02240000
distStartDA	dc.l	$00065300

;----------------------------------------------------------
; params:
;  a0 - wave ptr
; returns:
;  d0.w - updated wave evaluation
update_wave:
	move.l	a1,-(sp)
	lea		sintab,a1
	moveq	#0,d0
	move.w	waveDeg(a0),d0
	add.w	waveDegDelta(a0),d0
	move.w	d0,waveDeg(a0)
	lsr.w	#7,d0
	; get sine value
	;andi.w	#$ff,d0
	add.w	d0,d0
	move.w	(a1,d0.w),d0	; sin(waveDeg) -> d0
	muls.w	waveAmp(a0),d0
	swap	d0				; new position in d0
	move.l	(sp)+,a1

	rts


;----------------------------------------------------------
ballz:
	; move ball..
	lea		ball_pos,a1

	lea		4(a1),a0		; wave data ptr in a1


	bsr.s	update_wave		; wave x 1
	move.w	d0,d1			; x in d2
	lea		wave_size(a0),a0
	bsr.s	update_wave		; wave x 1
	add.w	d0,d1			; x in d2
	add.w	#160-16,d1		; center on screen

	move.w	d1,d2


	; get ptr to preshifted sprite
	andi.w	#$f,d1
	add.w	d1,d1
	add.w	d1,d1
	lea		sprt1_shift_list,a1
	move.l	(a1,d1),a1

	; calculate offset on screen
	lsr.w	#4,d2		; d2/16
	;andi.w	#$f,d2
	lsl.w	#3,d2		; d2*8


	; y waves
	lea		wave_size(a0),a0
	bsr 	update_wave		; wave x 1
	move.w	d0,d1			; x in d2
	lea		wave_size(a0),a0
	bsr 	update_wave		; wave x 1
	add.w	d0,d1			; x in d2
	add.w	#100-16,d1		; center on screen
	move.w	d1,d0
	lsl.w	#2,d1			; (y = ((y*8)+y)*32 = y*128 + y*32 = y*(128+32) = y*160
	add.w	d0,d1
	lsl.w	#5,d1
	add.w	d1,d2



	move.l	screen_ptrs,a0
	lea		(a0,d2),a0

	; blit loop
	moveq	#32-1,d0
.blit_row
	; MASK
	move.l	a0,a2
	move.w	(a1)+,d1

	and.w	d1,(a2)+
	and.w	d1,(a2)+
	and.w	d1,(a2)+
	and.w	d1,(a2)+

	move.w	(a1)+,d1

	and.w	d1,(a2)+
	and.w	d1,(a2)+
	and.w	d1,(a2)+
	and.w	d1,(a2)+

	move.w	(a1)+,d1

	and.w	d1,(a2)+
	and.w	d1,(a2)+
	and.w	d1,(a2)+
	and.w	d1,(a2)+

	; GFX
	move.l	(a1)+,d1
	or.l	d1,(a0)+
	move.l	(a1)+,d1
	or.l	d1,(a0)+
	move.l	(a1)+,d1
	or.l	d1,(a0)+
	move.l	(a1)+,d1
	or.l	d1,(a0)+
	move.l	(a1)+,d1
	or.l	d1,(a0)+
	move.l	(a1)+,d1
	or.l	d1,(a0)+

	lea		160-24(a0),a0
	dbra.w	d0,.blit_row

	rts

;----------------------------------------------------------
	section data
;----------------------------------------------------------
	rsreset
waveDeg			rs.w	1
waveDegDelta	rs.w	1
waveAmp			rs.w	1
wave_size		rs.b	0


	rsreset
smLoop		rs.l	1
smSetup		rs.l	1
smFrames	rs.l	1


ball_pos	dc.w	100,100

b_xs1d	dc.w	100
b_xs1s	dc.w	$0130
b_xs1a	dc.w	200

b_xs2d	dc.w	128
b_xs2s	dc.w	$01c0
b_xs2a	dc.w	(120-32)/2

b_ys1d	dc.w	50
b_ys1s	dc.w	$01e7
b_ys1a	dc.w	100

b_ys2d	dc.w	128
b_ys2s	dc.w	$0088
b_ys2a	dc.w	100-32


vbl_count dc.l	0

palette:
	incbin	"ball.plt"
	dc.w	$000,$111,$222,$333,$444,$555,$666,$777
	dc.w	$111,$222,$333,$444,$555,$666,$777,$707

bg:	dc.w	%0101010101010101
	dc.w	%0011001100110011
	dc.w	%0000111100001111
	dc.w	%1111111111111111

sintab:	incbin	"sintab.bin"

ball:	incbin	"ball.bin"


	even
vulk:
	incbin	"vulk.bin"

music:
	incbin	"LOADER.SND"

;----------------------------------------------------------
	section bss
;----------------------------------------------------------

dist_ptr_use	ds.l	1
dist_ptr	ds.l	2

vulk_a		ds.w	1

sprt1_shift_list:
	ds.l	16

sprt1_preshift:
	ds.w	(24*32+6*32)*16	; added space for preshifted mask


screen_ptrs
	ds.l	8

color_ptr
	ds.l	1

	even

color_dist
	ds.w	200*2

color_data
	ds.w	8*228*2
