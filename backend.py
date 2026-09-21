from flask import Flask, render_template, request
import numpy as np
import matplotlib.pyplot as plt
from cubiomespi import Generator, Dimension,get_biome_at, MCVersion #needed to compute the world using the minecraft seed
from random import randint
import json
from PIL import Image
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
    

    seed = int(request.form.get("seed"))
    version = request.form.get("version")
    dimension = request.form.get("dimension")
    scale = int(request.form.get("scale"))
    dimension = dimensions[dimension]
    height = scale
    width = int(round(scale * 2, 0))
    startx = 0
    startz  = 0
    #cubiomes gen pipeline
    version_correct = version.replace(".","_")
    version_correct = getattr(MCVersion, "MC_" + version_correct)
    batch = 50
    gen = Generator(version_correct, seed, dimension)
    grid_width = len(range(startx,startx + width, batch ))
    grid_height = len(range(startz,startz + height, batch))

    grid = np.zeros((grid_width, grid_height))
    colour = np.zeros((grid_width, grid_height,3))


    for i, x in enumerate(range(startx, startx + width, batch)):
        for a, z in enumerate(range(startz, startz + height,batch )):
            grid[i, a] = get_biome_at(gen, x, 0, z)#get_biome_at is imported from cubiomespi to calculate the exact block biome.
    for biome_id, color in BIOME_COLORS.items():
        colour[grid == int(biome_id)] = color 
    colour = colour / 255.0
    #the rendering using matplotlib:
    plt.figure()
    plt.imshow(colour.transpose(1,0,2), origin='lower', extent = [startx, startx +width, startz, startz +height])
    plt.savefig('static/map.png')

    img = Image.open("static/map.png")
    width_px, height_px = img.size
    res = img.crop((0, 90, width_px, height_px -60))
    res.save("static/map.png")
    plt.close()
    return render_template("index.html",random=randint(1,10000))
if __name__ == "__main__":
    app.run(debug=True)