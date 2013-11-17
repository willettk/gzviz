import json
import random
import colorbrewer
import itertools
import numpy as np

from astropy.io import fits
from collections import Counter

# Determine the number of unique morphological classes from GZ2 and the number
# of galaxies in each respective class

def collate_classes():

    fitsfile = 'gz2class.fits'
    with fits.open('gz2class.fits') as p:
        data = p[1].data

    gz2class_cnt = Counter(data['gz2class'])

    return gz2class_cnt

# Determine HTML-compliant hex numbers for the RGB triplets returned by colorbrewer

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x+y for x in _NUMERALS for y in _NUMERALS)}
LOWERCASE, UPPERCASE = 'x', 'X'

def triplet(rgb,lettercase=UPPERCASE):

    return format((rgb[0]<<16 | rgb[1]<<8 | rgb[2]), '06'+lettercase)

# Find the URL for the SkyServer image of an example galaxy in each morphological class

def unique_gz2(cnt):

    fitsfile = 'gz2class.fits'
    with fits.open('gz2class.fits') as p:
        data = p[1].data

    image_dict = {}

    # Loop over unique classes
    for c in cnt:
        matched = (data['gz2class'] == c)
        ind = random.randint(0,np.sum(matched))-1

        # Global image parameters
        imgsize=424
        scale = 0.5

        # Specific parameters for this galaxy
        ra = data[matched][ind]['ra']
        dec = data[matched][ind]['dec']
        size = data[matched][ind]['PETROR90_R']

        imgsizex = imgsizey = imgsize
        imgscale = size * 0.02 * scale
        info = {'ra':ra, 'dec':dec, 'scale':imgscale,
                'imgsizex':imgsizex, 'imgsizey':imgsizey}

        urlformat = 'http://casjobs.sdss.org/ImgCutoutDR7/getjpeg.aspx?ra=%(ra).6f&dec=%(dec).6f&scale=%(scale).6f&width=%(imgsizex)i&height=%(imgsizey)i'
        url = (urlformat % info)

        # Add URL as a key:value pair to the dictionary
        image_dict[c] = url
        
    return image_dict

# Make the JSON data file that will be embedded in the HTML page for d3 visualization

def make_json(cnt,image_dict):

    gallist = []
    palette = colorbrewer.PuRd[8]
    for gclass,ngal in cnt.iteritems():

        # Pick color based on length of string (somewhat akin to "complexity" of morph.)

        color = triplet(palette[len(str(gclass))-1])

        # Add data in dictionary format
        tempdata = {'playcount':str(ngal),
                    '$color':'#%s' % color,
                    "image": image_dict[gclass],
                    '$area':ngal}
        tempgal = {'children':[],
                    'data':tempdata,
                    'id':'gal_%s' % gclass,
                    'name':'%s' % gclass}

        gallist.append(tempgal)
        
    # Set up the root node

    allgals = {'children':gallist,'data':{},'id':'root','name':'Galaxy Zoo 2'}

    # Dump all galaxies to one big JSON
    with open('gz2.json','w') as f:
        json.dump(allgals,f)

    return allgals

# Write the Javascript file that will be run by the HTML page

def write_js(j):

    a,b = open('half1.js','r'),open('half2.js','r')

    with open('gz2.js','w') as file:
        file.write(a.read())
        file.write('var json = ')
        json.dump(j,file)
        file.write(b.read())
        
    a.close()
    b.close()

# Run all tasks in the module if called from command line

if __name__ == '__main__':

    cnt = collate_classes()
    image_dict = unique_gz2(cnt)
    allgals = make_json(cnt,image_dict)
    write_js(allgals)

