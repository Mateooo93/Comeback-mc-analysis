from flask import Flask, render_template, request
import numpy as np
from flask_socketio import SocketIO, emit
import matplotlib.pyplot as plt
from cubiomespi import Generator, Dimension,get_biome_at, MCVersion, Structure, find_structure_in_range, get_stronghold_pos #needed to compute the world using the minecraft seed
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
socketio = SocketIO(app)
gen = None
@app.route("/", methods=["GET"])
def index():
    return(render_template("index.html"))

@socketio.on("coordinates")
def handle_coordinates(data):
    x = data["x"]
    z = data["z"]
    biome = get_biome_at(gen,x, 0, z )
    BIOMES = json.load(open("biomes_map.json"))
    biome_name = BIOMES.get(str(biome), "Unknown")
    emit("biome", {"biome": biome_name})
    return 

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
    show_outposts = request.form.get("outposts")
    if show_outposts == None:
        show_outposts = False
    else:
        show_outposts = True
    show_strongholds = request.form.get("strongholds")
    if show_strongholds  == None:
        show_strongholds = False
    else:
        show_strongholds = True
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
    batch = max(1, scale // 300)
    global gen
    gen = Generator(version_correct, seed, dimension)
    start =time.time()

    outposts = []
    outposts = find_structure_in_range(gen, Structure.Outpost, startx, startz, startx + width, startz+ height) 
    if outposts == None:
        outposts = []

    villages = []
    villages = find_structure_in_range(gen, Structure.Village, startx, startz, startx + width, startz+ height) 
    if villages == None:
        villages = []

    strongholds = []
    if show_strongholds == True:
        count = max(128, int(scale/ 1000) ** 2 *128)
        strongholds = get_stronghold_pos(gen, count)
        strongholds_list = []
        for x, z in strongholds:
            if startx <= x <= startx + width and startz <= z <= startz + height:
                strongholds_list.append((x,z))
        strongholds = strongholds
    if strongholds == None:
        strongholds = []

    grid_width = len(range(startx,startx + width, batch ))
    grid_height = len(range(startz,startz + height, batch))
    print("structures: ",time.time() -start, "seconds")
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
    pillage_image = plt.imread("static/pillager.png")
    stronghold_image = plt.imread("static/stronghold.jpeg")

    icon_zoom = 0.013
    if scale > 30000:
        icon_zoom = 0.007
    if scale > 80000:
        icon_zoom = 0.002
    fig, ax = plt.subplots()
    ax.imshow(colour.transpose(1,0,2), origin='lower', extent = [startx, startx +width, startz, startz +height])
    fig.subplots_adjust(left=0.23)
    fig.canvas.draw()

    start = time.time()
    if villages != [] and show_villages == True:
        for x, z in villages:
            image = OffsetImage(village_image, zoom= icon_zoom)
            annotation = AnnotationBbox(image,(x,z), frameon=True, pad= 0.1)
            ax.add_artist(annotation)
        legend_image = OffsetImage(village_image, zoom= 0.03)
        annotation = AnnotationBbox(legend_image,(0.025, 0.7),xycoords=fig.transFigure,frameon=True,pad=0.2)
        fig.add_artist(annotation)
        fig.text( 0.050, 0.7, "Villages", va= "center", fontsize = 8)
    print("villages rendering: ",  time.time() -start, " seconds")
    if outposts != [] and show_outposts == True:
        start = time.time()
        for x, z in outposts:
            image = OffsetImage(pillage_image, zoom= icon_zoom)
            annotation = AnnotationBbox(image,(x,z), frameon=True, pad= 0.1)
            ax.add_artist(annotation)
        legend_image = OffsetImage(pillage_image, zoom=0.03)
        annotation = AnnotationBbox(legend_image,(0.025, 0.65),xycoords=fig.transFigure,frameon=True,pad=0.2)
        fig.add_artist(annotation)
        fig.text( 0.050, 0.65, "Pillages", va= "center", fontsize = 8)
    print("outposts rendering: ",  time.time() -start, " seconds")

    if strongholds != [] and show_strongholds == True:
        start = time.time()
        for x, z in strongholds:
            image = OffsetImage(stronghold_image, zoom= icon_zoom)
            annotation = AnnotationBbox(image,(x,z), frameon=True, pad= 0.08)
            ax.add_artist(annotation)
        legend_image = OffsetImage(stronghold_image, zoom=0.03)
        annotation = AnnotationBbox(legend_image,(0.025, 0.60),xycoords=fig.transFigure,frameon=True,pad=0.14)
        fig.add_artist(annotation)
        fig.text( 0.050, 0.60, "strongholds", va= "center", fontsize = 8)
    print("strongholds rendering: ",  time.time() -start, " seconds")



    dpi =400


    plt.savefig('static/map.png', dpi=dpi)
    img = Image.open("static/map.png")
    print("PNG size:", img.size)
    width_px, height_px = img.size
    top_crop = int(200* dpi/200)
    bottom_crop = int(100* dpi/200)

    bbox = ax.get_window_extent()
    print("map bounds(pixels):",bbox.x0, bbox.y0, bbox.x1, bbox.y1)
    scale_factor = dpi / 100
    left = bbox.x0*scale_factor
    bottom = height_px -bbox.y0*scale_factor-top_crop
    right = bbox.x1*scale_factor
    top = height_px -bbox.y1*scale_factor-top_crop

    res = img.crop((0, top_crop, width_px, height_px -bottom_crop))
    res.save("static/map.png")
    plt.close()
    
    return render_template("index.html",random=randint(1,10000), startX=startx, startZ=startz, width=width, height=height, mapLeft=left,mapTop=top,mapRight=right,mapBottom=bottom)
if __name__ == "__main__":
    socketio.run(app, debug=True)