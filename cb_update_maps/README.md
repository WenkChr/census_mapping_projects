# New cb Geometry Mapping

## Description

This project adds in new cb geometry and labels under the old cb geometry so that any changes are clearly visible. The changed maps can then be saved to a pdf using the pdf saver script provided. This project was created using python 2.7 and arcmap 10.6

## Process

### Data Prep and Processing

As this project takes maps that have been output by GMS please only use maps that are the final output as the added data here will not be maintained after being run through GMS again. There is only one major preprocessing step for this project and that is to setup the symbology layer that will be used in all the maps. To do this open the new cb geometry layer in arcmap and make the changes so that it fit as desired. 

![Example Symbology Image](images/new_cb_symbology.PNG)

### extract_all_zips.py

### augment_maps.py

### zip_mxds.py

### mxd_to_pdf.py

If the desired output is a pdf instead of a zipped mxd / mdb pair then run this script with the input as the directory of the imported maps. The directory must contain folders names like the image below

![PDF output file structure](imagess/pdf_desired_output.png)

The output directory must be organized like this because the script determines outpath by looking at this dectionary:
    
    destination_dict = {'10': 'Halifax',
                        '11': 'Halifax',
                        '12': 'Halifax',
                        '13': 'Halifax',
                        '24': 'Montreal',
                        '35': 'Toronto',
                        '46': 'Edmonton',
                        '47': 'Edmonton',
                        '48': 'Edmonton',
                        '59': 'Vancouver',
                        '60': 'Vancouver',
                        '61': 'Edmonton',
                        '62': 'Edmonton'} 

The numbers are the province code of the mxd and the city is the destination city the map will be sent to.