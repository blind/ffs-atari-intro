#!/usr/bin/env python

import sys
import base64
import os
import struct
import optparse
import json
from xml.dom import minidom
from xml.etree import ElementTree

try:
	import Image
	import ImagePalette
except Exception,e:
	from PIL import Image
	from PIL import ImagePalette

try:
	from cStringIO import StringIO
except Exception,e:
	from StringIO import StringIO

def subimages(image, sx, sy, w, h, cx = 1, cy = 1):
	blocks = []
	for y in xrange(cy):
		for x in xrange(cx):
			box = (sx+w*x, sy+h*y, sx+w*x+w, sy+h*y+h )
			sub = image.crop( box )
			blocks.append(sub)
	return blocks

def strip_bitplanes_interleaved( input_data, planes_to_keep_mask ):
	return input_data


def converttobitplanes( image, bp_count = 4, bits_per_plane = 8 ):
	width,height = image.size
	output = StringIO()
	for h in xrange(0,height ):
		for w in xrange( 0,width, bits_per_plane ):
			bps = [ 0 for x in xrange(0,bp_count)]
			for pix in xrange( w, w+bits_per_plane ):
				pixelData = image.getpixel((pix,h))
				## Shift previous pixels.
				for i in xrange(0,bp_count): bps[i] = bps[i]<<1

				for i in xrange(0,bp_count): bps[i] |= (1 if (pixelData & 1<<i) else 0)

			if bits_per_plane == 8:
				f = r">%dB"
			elif bits_per_plane == 16:
				f = r">%dH"
			#for i in xrange(0,bp_count):
			output.write( struct.pack( f%(bp_count), *bps ) )

	return output.getvalue()

def generatemaskfrombitplanes( bitplanedata, bp_count  = 4, bits_per_plane = 8 ):
	data = StringIO(bitplanedata)
	outdata = StringIO()
	chunk_size = bp_count * (bits_per_plane/8)

	if bits_per_plane == 16:
		ifmt = ">%dH"%bp_count
		ofmt = ">H"
	elif bits_per_plane == 8:
		ifmt = ">%dB"%bp_count
		ofmt = ">B"
	else:
		raise( "Invalid bits per plane count %d"%bits_per_plane )

	while True:
		block = data.read(chunk_size )
		if not block:
			break
		msk = 0
		# print( ifmt, len(block), chunk_size )
		planes = struct.unpack( ifmt, block )
		for m in planes:
			msk |= m
		outdata.write(struct.pack(ofmt,msk))
	return outdata.getvalue()

open_images = {}

def open_image( filename ):
	if filename in open_images:
		return open_images[filename]
	inputfile = open( filename,"rb" )
	image = Image.open(inputfile)
	open_images[filename] = image
	image.seek(0)
	return image

def gen_tiledata(part,*params):
	print( "reading %s"%(part["source"]))
	image = open_image(part["source"])
	if image.mode != 'P':
		image = image.convert('P')

	tw = part["tile_width"]
	th = part["tile_height"]

	x,y = part["block"][0]
	cx,cy = part["block"][1]

	tiles = subimages(image, x*tw, y*th, tw, th, cx, cy )

	data = StringIO()

	for tile in tiles:
		tile.load()
		if tile.mode != 'P':
			raise Exception("Invalid mode %s for bitplane conversion"%tile.mode)
		converted = converttobitplanes( tile, 4, 16 )
		data.write(converted)

	outfile = open( part["output"], "wb")
	outfile.write(data.getvalue())
	outfile.close()

def gen_colorblock(part, *params):
	image = open_image(part["source"])

	x = part["x"]
	y = part["y"]

	w = part["width"]
	h = part["height"]

	block = subimages(image,x,y,w,h)[0]
	block.load()
	p = block.getpalette()

	colordata = []

	f = lambda x: x

	if image.mode == 'P':
		# paletted
		f = lambda x: p[x*3:x*3+3]

	for y in xrange(0, h):
		for x in xrange(0, w):
			pixel = block.getpixel((x,y))
			rgb = f(pixel)
			stecol = rgb2ste(*rgb)

			colordata += [stecol]

	outfile = open( part["output"], "wb")
	outfile.write( struct.pack(">%dH"% len(colordata) ,*colordata ))
	outfile.close()



def gen_palette(part,*params):
	image = open_image(part["source"])
	if image.mode != 'P':
		print("error, needs pallette based image")
		exit(23)
	p = image.getpalette()
	start = 0
	end = 16
	if "start" in part:
		start = int(part["start"])
	if "end" in part:
		end = int(part["end"])
	l = []
	output = open(part["output"], "wb" )
	for i in xrange(start,end):
		c = i*3
		stecol = rgb2ste(*p[c:c+3])
		output.write( struct.pack(">H", stecol ))
	output.close()

def rgb2ste(r,g,b):
	r = ((r) >> 4) & 15
	g = ((g) >> 4) & 15
	b = ((b) >> 4) & 15
	r = (r>>1) | ((r&1)<<3)
	g = (g>>1) | ((g&1)<<3)
	b = (b>>1) | ((b&1)<<3)
	return (r<<8) |(g<<4)|b


def gen_masks(part,*params):
	print( "reading %s"%(part["source"]))
	image = open_image(part["source"])
	tw = part["tile_width"]
	th = part["tile_height"]

	x,y = part["block"][0]
	cx,cy = part["block"][1]

	tiles = subimages(image, x*tw, y*th, tw, th, cx, cy )

	data = StringIO()

	for tile in tiles:
		tile.load()
		converted = converttobitplanes( tile, 5, 16 )
		data.write(converted)

	data = generatemaskfrombitplanes(data.getvalue(),5,16)
	with open(part["output"],"wb") as outfile:
		outfile.write(data)


#def map_loader(part):
#	pass

def map_loader(part,*params):
	root = ElementTree.parse( part["source"])
	layer = root.find(".//layer[1]")
	# TODO: add to part definition what layer to save as what file
	data = layer.find(".//data[1]")
	enc = data.attrib["encoding"]
	if enc == "base64":
		tmap = base64.b64decode( data.text )
		mbytes = len(tmap)
		tiles = struct.unpack( "<%dI"%(mbytes/4), tmap)

	else:
		print("Unsupported map format")
		exit(2)

	mapwidth = int(layer.attrib["width"])
	firstgid = int(root.find(".//tileset[1]").attrib["firstgid"])

	result = (tiles,mapwidth,firstgid, root)

	for room in part["subtasks"]:
		dispatch( room, result )
	return result

def gen_collisionmask(part,inp):
	(tiles,mapwidth,firstgid,xmlroot) = inp
	solidTiles = xmlroot.findall(".//tile//property[@name='solid'][@value='true']/../..")
	solidTileIds = [int(t.attrib['id']) for t in solidTiles]
	# print part["block"]
	(sx,sy),(w,h) = part["block"]
	# print "solid tiles are: %s"%solidTileIds

	bits = []
	for y in xrange(sy,sy+h):
		mask = 0
		for x in xrange(sx,sx+w):
			tidx = y*mapwidth + x
			if (tiles[tidx]-firstgid) in solidTileIds:
				mask |= (1<<(31-(x-sx)))
				#print tidx, (x,y), tiles[tidx]
		bits.append(mask)
		# print "{0:032b}".format(mask)

	# Save to output
	outfile = open( part["output"],"wb")
	outfile.write( struct.pack(">%dL"%(len(bits)), *bits))

def gen_room(part,inp):
	(tiles,mapwidth,firstgid,xmlroot) = inp
	(px,py),(w,h) = part["block"]
	roomtiles = []
	for y in xrange(0,h):
		for x in xrange(0,w):
			tidx = px+(y+py)*mapwidth + x
			roomtiles.append( tiles[tidx]-firstgid )

	room_dest = open( part["output"], "wb" )
	room_dest.write( struct.pack(">%dB"%(w*h), *roomtiles ))
	room_dest.close()


def dispatch( part, inp = None ):
	dispatch_tab = {
			"tiledata" : gen_tiledata,
			"palette"  : gen_palette,
			"masks"    : gen_masks,
			"maploader": map_loader,
			"collisionmask": gen_collisionmask,
			"room"     : gen_room,
			"colorblock" : gen_colorblock,
		}
	ptype = part["type"]
	if ptype in dispatch_tab:
		dispatch_tab[ptype](part, inp)
	else:
		print( "Errorror, unknown type %s"%(ptype))
		exit(4)

def main():

	parser = optparse.OptionParser()
	parser.add_option("-c", "--clean", action="store_true", dest="clean", default=False, help="Delete all output file defined in definitions file")
	parser.add_option("--deps", action="store", dest="depsout", default=None, help="Generate deps file for Make rules")

	(opts,args) = parser.parse_args()

	if len(args) != 1:
		print( "usage: <definition file>")
		sys.exit(-1)

	if not os.path.exists( args[0] ):
		print("definition file could not be found")
		sys.exit(-2)

	def_file = open( args[0],"r")

	definition = json.load( def_file )



	if opts.depsout != None:
		print("Deps not yet implemented")
		exit(1)

	if opts.clean:
		outputs = []
		for part in definition:
			find_output(part, outputs)

		for filename in outputs:
			try:
				os.remove( filename )
				print "Deleted " + filename
			except Exception,e:
				pass
		exit(0)

	for part in definition:
		dispatch(part)

def find_output(part, outputs):
	if "output" in part:
		outputs.append( part["output"] )
	if "subtasks" in part:
		for subpart in part["subtasks"]:
			find_output( subpart, outputs )

if __name__ == '__main__':
	main()

