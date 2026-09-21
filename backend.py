from flask import Flask, render_template, request
import numpy as np
import matplotlib.pyplot as plt
from cubiomespi import Generator, Dimension,get_biome_at, MCVersion, Structure, find_structure_in_range #needed to compute the world using the minecraft seed
from random import randint
import json
from PIL import Image
import time
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.cbook import get_sample_data
from matplotlib.transforms import TransformedBbox, Bbox
from matplotlib.image import BboxImage
from matplotlib.legend_handler import HandlerBase
app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return(render_template("index.html"))
@app.route("/mapgen", methods=["POST"])
#first of all we're gonna render a minecraft map using its seed
def map():
    BIOME_COLORS = json.load(open("biomes.json"))


    #turn the response from the form to the right format according to cubiomes
    dimensions = {
        "overworld": Dimension.DIM_OVERWORLD,
        "nether": Dimension.DIM_NETHER,
        "end": Dimension.DIM_END
    }
    show_villages = request.form.get("villages")
    if show_villages == None:
        show_villages = False
    else:
        show_villages = True
    print("show_villages: ", show_villages)
    xcoord = int(request.form.get("X")or 0)
    zcoord =int(request.form.get("Z") or 0)
    seed = int(request.form.get("seed"))
    version = request.form.get("version")
    dimension = request.form.get("dimension")
    scale = int(request.form.get("scale"))
    dimension = dimensions[dimension]
    height = scale
    width = int(round(scale * 2, 0))

  
    startx = xcoord
    startz = zcoord
    #cubiomes gen pipeline
    version_correct = version.replace(".","_")
    version_correct = getattr(MCVersion, "MC_" + version_correct)
    batch = max(1, scale // 200)
    gen = Generator(version_correct, seed, dimension)
    start =time.time()
    villages = []
    villages = find_structure_in_range(gen, Structure.Village, startx, startz, startx + width, startz+ height) 

    if villages == None:
        villages = []

    grid_width = len(range(startx,startx + width, batch ))
    grid_height = len(range(startz,startz + height, batch))
    print("villages: ",time.time() -start, "seconds")
    grid = np.zeros((grid_width, grid_height))

    colour = np.zeros((grid_width, grid_height,3))


    start =time.time()
    for i, x in enumerate(range(startx, startx + width, batch)):
        for a, z in enumerate(range(startz, startz + height,batch )):
            grid[i, a] = get_biome_at(gen, x, 0, z)#get_biome_at is imported from cubiomespi to calculate the exact block biome.
    print("biomes: ", time.time( )- start ,"seconds")
    for biome_id, color in BIOME_COLORS.items():
        colour[grid == int(biome_id)] = color 
    colour = colour / 255.0




    #the rendering using matplotlib:
    village_image = plt.imread("static/villager.jpeg")
    fig, ax = plt.subplots()
    ax.imshow(colour.transpose(1,0,2), origin='lower', extent = [startx, startx +width, startz, startz +height])
    fig.subplots_adjust(left=0.23)
    if villages != [] and show_villages == True:
        for x, z in villages:
            image = OffsetImage(village_image, zoom= 0.013)
            annotation = AnnotationBbox(image,(x,z), frameon=True, pad= 0.1)
            ax.add_artist(annotation)
        legend_image = OffsetImage(village_image, zoom=0.03)
        annotation = AnnotationBbox(legend_image,(0.025, 0.7),xycoords=fig.transFigure,frameon=True,pad=0.2)
        fig.add_artist(annotation)
        fig.text( 0.050, 0.7, "Villages", va= "center", fontsize = 8)
    dpi =400
    plt.savefig('static/map.png', dpi=dpi)
    img = Image.open("static/map.png")
    width_px, height_px = img.size
    top_crop = int(200* dpi/200)
    bottom_crop = int(100* dpi/200)


    res = img.crop((0, top_crop, width_px, height_px -bottom_crop))
    res.save("static/map.png")
    plt.close()
    
    return render_template("index.html",random=randint(1,10000))
if __name__ == "__main__":
    app.run(debug=True)