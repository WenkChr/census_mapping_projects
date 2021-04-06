# NT ATLAS Maps

## Description

This project took maps output by GMS and applied open data layers from the NWT ATLAS to enhance
map readability by giving field staff more points of reference via open data. These enhancements 
were done to mirror similar maps produced by NWT.In order to do the enhancements a process was 
developed using python using arcpy which would makethe enhancements and save an enhanced copy 
in a new directory.

## Process

As this project uses arcmap all scripting is done in python 2.7. Below is a brief description of each step
and file in the process.

### Data Prep and Preprocessing

There are several steps that must be completed before running the process. First all enhancement data
needs to be downloaded from the NWT ATLAS. The ATLAS viewer can be located here and all layerrs are available 
for free download: https://www.maps.geomatics.gov.nt.ca/HTML5Viewer_Prod/index.html?viewer=ATLAS  

The specific layers to download for this project are. Ensure that you select the entire territory for best
coverage in augmenting maps:
    
- Building Footprints
- Surveyed Parcels
- Transportation Polygons (specifically for airstrips)
- Structure Points
- Unsurveyed Tenured Commissioners Land

The other data source used to imporve the maps was address point data sourced from the city of yellowknife
which can be found at the following link: 

https://opendata.yellowknife.ca/home/details/92407f76-6c52-449a-a4c3-01fbdc3b30ff

if the link is broken the data is found in the open data section of the site under civic addresses and is a
point file. For the purposes of the script it is best to download the file geodatabase version of the file.

Once the data is downloaded layer specific symbology and labeling symbology needs to be applied. To do this 
open an empty arcmap session to be a layer workspace and add the ATLAS layers to the data frame.

Apply the desired symbology and label settings to each ATLAS layer and any of the standard GMS layers
as needed. Export each layer as a .lyr file into the same folder.

Once all preperations are complete you can input the paths to the correct folders and files into the variables
in the inputs section of the project scripts 

### extract_all_zips.py

MXD's received from GMS were received as zip files this script contains a function that
unzips the contents of a zip and puts all outputs into a single folder.

### augment_maps.py

The main augmentation script and takes unzipped mxd and mdb files from a single folder. Iterates over
all map documents in the specified folder and outputs an augmented copy in a new folder with an
updated copy of the associated mdb.

### zip_mxds.py

Takes all mxd’s and associated mdb’s in a single folder and creates a zip containing the mxd and
associated mdb. Outputs everything into a single folder.