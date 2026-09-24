This is repository lets you visualize a minecraft map using its seed and version
but it's still a work in progress, it uses flask so you have a nice interface with inputs such as

scale: controls how many blocks you want rendered, 
seed: controls the map seed 
and 
version: controls the version the map was made in
Villages: you also have the possibility to see villages in the map
Outposts: you also have the possibility to see Outposts in the map
Strongholds: you also have the possibility to see Strongholds in the map

this was made using matplotlib, flask and cubiomespi,
cubiomespi is neccesary to generate the world using the seed and minecraft version
flask is used to send the data from the python backend to the interface
this allows the users to have an nice html interface without relying on a terminal

you can also see what coordinate your mouse is pointing at (in minecraft) aswell as its corresponding biome

the css was highly inspired by the one hackclub uses which is open source: (https://css.hackclub.com/), 
except for the font which is exclusively reserved for hackclub hq sites.




