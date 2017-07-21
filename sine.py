import math
import struct

a = 32767; l = 256
sintab = [math.sin(x*(math.pi*2)/l)*a for x in xrange(0,l)]
f = open("sintab.bin","wb")
f.write( struct.pack(">%dh"%len(sintab), *sintab))
f.close()

