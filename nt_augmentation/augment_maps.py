import arcpy
import sys
import os
import arcpy.mapping as mp
import shutil
import pandas as pd
import time
'''
This script is to perform enhancements on NWT distrbution maps by adding NWT ATLAS data and Yellowknife address point
data to the distribution maps. The steps of the script are as follows:

1,) get a list of the mxd's from the directory

2.) For each mxd in the directory determine the location, scale and type of map in order to set the input datasets to be 
    added. Also determine whether to add layers based on the extent of the map frame

3.) Add layers to the map and set standardized colours and labels to them in order to ensure consistency of symbology 
    over all the maps in the set. Swap sources so that the layers point to the datasets in the map specific mdb

4.) Change the symbology of the cu cb layers  
   
5.) Save augmented mxd as a new document to ensure repeatability should parameters change or redo's need to be done

'''
arcpy.env.overwriteOutput = True
# ----------------------------------------------------------------------------------------------------------------------
# Functions


def list_directory_files(directory_path, file_extension):
    # returns a list of all file paths with a specific extension from the given directory
    return_list = []

    # check to ensure directory exists
    if not os.path.exists(directory_path):
        print 'Given directory does not exist check inputs'
        sys.exit()

    # If the path exists then iterate over the directory and get all files with the specific file extension we want
    for o_file in os.listdir(directory_path):
        if o_file.endswith(file_extension):
            return_list.append(os.path.join(directory_path, o_file))

    return return_list


def getMapExtentPolygon(df, outGDB, outName= 'Visible_Extent_Polygon'):
    # Returns a polygon that matches the extent of the map for layer selection purposes

    # Get key info from dataframe
    extent = df.extent
    sr = df.spatialReference

    # Setup output polygon
    vis_ext_poly = os.path.join(outGDB, outName)
    arcpy.CreateFeatureclass_management(outGDB, outName, "POLYGON", spatial_reference=sr)


    # Get the corner points and add them to the array as point objects. create polygon from those points
    # Messy but easier to read like this
    XMAX = extent.XMax
    XMIN = extent.XMin
    YMAX = extent.YMax
    YMIN = extent.YMin
    pnt1 = arcpy.Point(XMIN, YMIN)
    pnt2 = arcpy.Point(XMIN, YMAX)
    pnt3 = arcpy.Point(XMAX, YMAX)
    pnt4 = arcpy.Point(XMAX, YMIN)
    array = arcpy.Array([pnt1, pnt2, pnt3, pnt4])
    polygon = arcpy.Polygon(array, sr)  # Creates polygon object
    arcpy.CopyFeatures_management(polygon, vis_ext_poly) # Add the new polygon to the empty feature class

    return vis_ext_poly # return the extent feature class


def checkForOverlap(mapExtentPolygon, layerList):
    # Checks if the layer falls into the map extent and if it does then it is retained if not it is not returned
    out_list = []
    for l in layerList:
        arcpy.SelectLayerByLocation_management(l, 'INTERSECT', mapExtentPolygon)
        if int(arcpy.GetCount_management(l)[0]) > 0:
            out_list.append(l)
        arcpy.SelectLayerByAttribute_management(l, selection_type='CLEAR_SELECTION')
    return out_list


def deleteExistingLegend(mxd):
    # Dictionary for the location of the legend in inches for each template coord 1- top left coord 2- bottom right
    #                                coord 1         coord 2
    template_legend_XY = {'11X17': [(5.50, 3.25), (8.00, 0.50)],
                          '17X11': [(13.75, 5.25), (16.5, 2.000)],
                          '17X22': [(10.5, 3.25), (14.0, 0.5)],
                          '22X17': [(18.74, 5.25), (21.5, 2.000)],
                          '22X34': [(16.5, 3.25), (19.00, 0.5)],
                          '34X22': [(30.75, 5.25), (33.5, 2.000)]}
    # Find all the elements that fall within the legend box for the specific template and delete or move them off map
    ex_text_element = mp.ListLayoutElements(mxd, 'TEXT_ELEMENT')[0]  # extract text element for type testing purposes
    for ele in mp.ListLayoutElements(mxd):
        # Extract xy coordinates for the template legend
        legendRange = template_legend_XY[template_type]
        xMinMax = [legendRange[0][0], legendRange[1][0]]
        yMinMax = [legendRange[0][1], legendRange[1][1]]
        # determine if anchor point falls within the legend box for the template
        if (min(xMinMax[0], xMinMax[1]) < ele.elementPositionX < max(xMinMax[0], xMinMax[1])) and \
                (min(yMinMax[0], yMinMax[1]) < ele.elementPositionY < max(yMinMax[0], yMinMax[1])):
            if not type(ele) == type(ex_text_element):  # text elements can't be groups so do this check first
                if ele.isGroup:  # grouped cannot be deleted so move off the page
                    ele.elementPositionX = 50.00  # New X coordinate for the group (inches)
                    ele.elementPositionY = 5.00  # New Y coordinate for the group (inches)
                    continue

            ele.delete()  # Delete non grouped elements that fall within the legend area


def addLayerToMDB(mdb, lyr):
    # Adds lyr file to the maps mdb and returns a path to the new fc
    arcpy.FeatureClassToFeatureClass_conversion(lyr, mdb, lyr.name)
    return os.path.join(mdb, lyr.name)


# ----------------------------------------------------------------------------------------------------------------------
# Inputs

# working_directory is where all the unzipped mxd's and mdb's are located
working_directory = 'INPUT PATH TO FOLDER CONTAINING EXTRACTED MXDS AND MDBS HERE'
# out_directory is where the augmented mdb's and mxd's will be placed
out_directory = 'INPUT PATH TO EMPTY OUTPUT DIRECTORY HERE'
# workingGDB will hold the map extent polygons and any other transitory products
workingGDB = 'INPUT PATH TO A WORKING/SCRATCH GDB HERE'

work_folder = "INPUT PATH TO WORK FOLDER PATH HERE"

# Style guides to extract the symbology and labels from
str_points_symb_lyr = os.path.join( work_folder, 'Structure_Points.lyr')
trp_poly_symb_lyr = os.path.join( work_folder, 'Transportation_Polygons.lyr')
bf_symb_lyr = os.path.join( work_folder, 'Building_Footprints.lyr')
sp_symb_lyr = os.path.join( work_folder, 'Surveyed_Parcels.lyr')
usp_symb_lyr = os.path.join( work_folder, 'Unsurveyed_Tenured_Commissioners_Land.lyr')
yk_adp_symb_lyr = os.path.join(work_folder,'yk_Address_Points.lyr')

# Layers with new symbology for select base layers

symb_lyr_basepath = work_folder
gms_base_symb_change = [os.path.join(symb_lyr_basepath, 'cu_al.lyr'),
                        os.path.join(symb_lyr_basepath, 'cb_al.lyr'),
                        os.path.join(symb_lyr_basepath, 'water_a.lyr'),
                        os.path.join(symb_lyr_basepath, 'water_l.lyr'),
                        os.path.join(symb_lyr_basepath, 'water_a_named.lyr'),
                        os.path.join(symb_lyr_basepath, 'water_l_named.lyr'),
                        ]

# Data to augment with
ATLAS_gdb = 'INPUT PATH TO DOWNLOADED ATLAS DATA HERE GDB PREFERRED'
yk_adp_GDB = 'INPUT PATH TO YELLOWKNIFE ADDRESS POINTS GDB HERE'
yk_adp_fc = 'INPUT PATH TO YELLOWKNIFE FEATURECLASS HERE'

# Map Scale Limiters
maxScaleLimit = 100000.0
bf_scale_limit = 8000.0
# ----------------------------------------------------------------------------------------------------------------------
# Logic
# Initial layer setup and prep
startTime = time.time() # capture start time
# Paths to layers that will be added
structure_points_fc = os.path.join(ATLAS_gdb, 'Structure_Points')
transport_polygons_fc = os.path.join(ATLAS_gdb, 'Transportation_Polygons')
building_footprints_fc = os.path.join(ATLAS_gdb, 'Building_Footprints')
surveyed_parcels_fc = os.path.join(ATLAS_gdb, 'Surveyed_Parcels')
unsurveyed_parcels_fc = os.path.join(ATLAS_gdb, 'Unsurveyed_Tenured_Commissioners_Land')

# Convert fc to layer and add a definition query where necessary
print 'Converting feature classes to layers'
print 'Converting structure points'
structure_points_lyr = mp.Layer(structure_points_fc)

print 'Converting Transportation Polygons'
transport_polygons_lyr = mp.Layer(transport_polygons_fc)

print 'Converting Building Footprints'
building_footprints_lyr = mp.Layer(building_footprints_fc)

print 'Converting Surveyed Parcels'
surveyed_parcels_lyr = mp.Layer(surveyed_parcels_fc)

print 'Converting Unsurveyed Parcels'
unsurveyed_parcels_lyr = mp.Layer(unsurveyed_parcels_fc)

print 'Converting Yellowknife address points'
yk_adp_lyr = mp.Layer(yk_adp_fc)

# Apply symbology from template .lyr file
print 'Compiling Style Guide'
lyr_style_guide = {'Building_Footprints': bf_symb_lyr,
                   'Surveyed_Parcels': sp_symb_lyr,
                   'Transportation_Polygons': trp_poly_symb_lyr,
                   'yk_Address_Points': yk_adp_symb_lyr,
                   'Structure_Points': str_points_symb_lyr,
                   'Unsurveyed_Tenured_Commissioners_Land': usp_symb_lyr
                   }
# Column order: mxd_name, total # of layers added,
aug_counts = {'Building_Footprints': 0,
              'Surveyed_Parcels': 0,
              'Transportation_Polygons': 0,
              'yk_Address_Points': 0,
              'Structure_Points': 0,
              'Unsurveyed_Parcels': 0,
              'Total_Maps_Augmented': 0
              }
# Create basic augmentation tracking doc lists holder
aug_tracking_rows = []

# iterate over the mxd's and augment
file_list = list_directory_files(working_directory, '.mxd')
for f in file_list:

    mxd_name = os.path.split(f)[1]  # Extract mxd name
    aug_track_row = [mxd_name]  # Create new row for tracking with the mxd name as  first item

    print 'Augmenting map #{} of {}'.format((file_list.index(f)) + 1, len(file_list))
    print 'MXD name: ' + mxd_name
    aug_counts['Total_Maps_Augmented'] += 1  # Adds the map to the total map count metric
    new_layers = [transport_polygons_lyr]  # New map layers list, layers here already aren't scale dependant

    # Setup new mdb for the mxd add the new layers to this document
    current_mdb_path = os.path.join(os.path.split(f)[0], os.path.split(f)[1].split('.')[0] + '.mdb')
    working_mdb_path = os.path.join(out_directory, os.path.split(current_mdb_path)[1].split('.')[0] + '.mdb')

    if os.path.exists(working_mdb_path): # if the mdb already exists delete it
        os.remove(working_mdb_path)
    working_mdb = shutil.copy(current_mdb_path, working_mdb_path)  # copy the working mdb over into the working folder

    # Setup all other important variables
    mxd = mp.MapDocument(f)  # open map doc

    print 'Resourcing database for existing layers'
    mxd.replaceWorkspaces(current_mdb_path, 'ACCESS_WORKSPACE', working_mdb_path, 'ACCESS_WORKSPACE')

    template_type = '{}X{}'.format(int(mxd.pageSize.width), int(mxd.pageSize.height))  # indicates the map template wXl

    df = mp.ListDataFrames(mxd)[0]  # Select the first df as there is only 1 in each map

    #Filter out pre-existing aug layers
    print "Removing layers from prior aug (if present)"
    remove_count = 0
    for lyr in mp.ListLayers(mxd, data_frame=df):
        aug_lyrs = ['Building_Footprints',
                   'Surveyed_Parcels',
                   'Transportation_Polygons',
                   'yk_Address_Points',
                   'Structure_Points',
                   'Unsurveyed_Parcels',
                   'Total_Maps_Augmented']
        if lyr.name in aug_lyrs:
            mp.RemoveLayer(df, lyr)
            remove_count += 1
    print str(remove_count) + " old aug layers removed"

    map_scale = df.scale

    print 'Map Scale: ' + str(int(map_scale))
    # if map_scale > maxScaleLimit:  # Maximum scale check so that we're not augmenting where not strictly necessary
    #     print 'Map scale beyond maximum scale. Map not augmented'
    #     os.remove(working_mdb_path)
    #     continue

    # Check map scale if scale is greater than threshold don't use certain layers
    if map_scale <= bf_scale_limit:
        new_layers.append(building_footprints_lyr)
        new_layers.append(structure_points_lyr)
        new_layers.append(surveyed_parcels_lyr)
        new_layers.append(unsurveyed_parcels_lyr)
        new_layers.append(yk_adp_lyr)

    print 'Creating map extent polygon'
    map_extent_poly = getMapExtentPolygon(df, workingGDB)  # Gets polygon of map extent for check of overlap with layers

    new_layers = checkForOverlap(map_extent_poly, new_layers)  # Checks layers in new_layers against map extent

    aug_track_row.append(len(new_layers))  # Adds total new layers added to the tracking doc
    lyr_names = sorted([str(lyr.name) for lyr in new_layers])  # Get a list of lyr names
    aug_track_row.append(str(tuple(lyr_names)))

    fc_list = []
    # Add layers in new_layers to copied mdb and then create a list of the layers to then add to the map
    # Project the layers so that the sr's match
    sr = df.spatialReference
    print 'Adding layers to map mdb and projecting them in the maps projection'
    for lyr in new_layers:
        fc = os.path.join(workingGDB, lyr.name + '_up')  # Convert to unprojected version
        arcpy.FeatureClassToFeatureClass_conversion(lyr, workingGDB, lyr.name + '_up')
        fc_sr = arcpy.Describe(fc).spatialReference
        geo_transformations = arcpy.ListTransformations(fc_sr, sr)
        fc_name = lyr.name  # For getting style guide reference
        prj_fc = os.path.join(working_mdb_path, fc_name)  # Path to projected fc

        if len(geo_transformations) > 0:
            # If there is a geo transformation required use it
            arcpy.Project_management(fc, prj_fc, sr, geo_transformations[0], fc_sr)
            fc_list.append(fc_name)
            continue
        # If no geo transformation required go ahead
        arcpy.Project_management(fc, prj_fc, sr)
        fc_list.append(fc_name)

    # Add the layers to the map and add to the top until new order decided

    print 'Adding {} new layers to map and applying symbology'.format(str(len(new_layers)))
    for fc in fc_list:
        # Convert to lyr then apply symbology then add to map
        lyr = mp.Layer(lyr_style_guide[fc])

        # For the below lyr types apply definition queries to remove non essential feature types
        # labeling is done here as well
        if lyr.name == 'Structure_Points':
            lyr.definitionQuery = "STRUCTURETYPE IN {}".format(str(tuple(['BTOWLIN',
                                                                          'BPOHLIN',
                                                                          'Antenna',
                                                                          'Sign'])))

        if lyr.name == 'Transportation_Polygons':
            lyr.definitionQuery = "TRANSPORTATIONTYPE = 'RRWYLIN'"

        #arcpy.ApplySymbologyFromLayer_management(lyr, lyr_style_guide[lyr.name])
        # This needs to stay below apply symbology layer because we're changing the lyr name
        mp.AddLayer(df, lyr, 'AUTO_ARRANGE')

        u_lyr = mp.ListLayers(mxd, lyr.name, df)[0]

        if u_lyr.name == 'Structure_Points':
            # moves structure points below the address range annotation to solve obscuring issue
            if len(mp.ListLayers(mxd, 'road_l_address_anno', df)) > 0: # check if road anno is actually in the map
                ref_lyr = mp.ListLayers(mxd, 'road_l_address_anno', df)[0]
                mp.MoveLayer(df, ref_lyr, u_lyr, 'AFTER')

        # Rename the unsurveyed parcels more concisely
        if u_lyr.name == 'Unsurveyed_Tenured_Commissioners_Land':
            u_lyr.name = 'Unsurveyed_Parcels'
            aug_counts['Unsurveyed_Parcels'] += 1  # Adds the lyr to the metrics counts
            continue  # this must always be the last thing done because of the name change in this part of the loop
        aug_counts[lyr.name] += 1  # Adds the lyr to the metrics counts

    # Check if there is yk_adp in the new layers. If there is adp will be labeled turn off the labels for sp
    if 'yk_Address_Points' in fc_list and 'Surveyed_Parcels' in fc_list:
        sp_lyr = mp.ListLayers(mxd, 'Surveyed_Parcels', df)[0]
        sp_lyr.showLabels = False

    # Change the symbology of select base map layers to match adjusted settings
    for l_path in gms_base_symb_change:
        lyr = mp.Layer(l_path)
        lyr_name = os.path.split(l_path)[1].split('.')[0]

        map_lyr = mp.ListLayers(mxd, lyr_name, df)

        if len(map_lyr) == 0:
            continue

        mp.UpdateLayer(df, map_lyr[0], lyr)
        del lyr

    # Replace lyr data sources with project mdb's
    mxd.replaceWorkspaces(ATLAS_gdb, 'FILEGDB_WORKSPACE', working_mdb_path, 'ACCESS_WORKSPACE')
    mxd.replaceWorkspaces(yk_adp_GDB, 'FILEGDB_WORKSPACE', working_mdb_path, 'ACCESS_WORKSPACE')

    print 'Exporting Map'
    # Required variables
    base_name = os.path.split(f)[1].split('.')[0]
    mxd_out_file = os.path.join(out_directory, '{}.mxd'.format(base_name))  # MXD out path
    # Save files logic
    mxd.saveACopy(mxd_out_file)  # Saves a copy of the augmented map to preserve original
    aug_tracking_rows.append(aug_track_row)  # Append the new tracking row to the tracking doc list
    del mxd
    del working_mdb_path

print 'Calculating Metrics'
# d is the basic outline of the metrics csv each layer name the total count of maps augmented
d = {'Layer': ['Building_Footprints',
               'Surveyed_Parcels',
               'Transportation_Polygons',
               'yk_Address_Points',
               'Structure_Points',
               'Unsurveyed_Parcels',
               'Total_Maps_Augmented']
     }
metrics_df = pd.DataFrame(d)
metrics_df['Maps Augmented'] = metrics_df['Layer'].map(aug_counts)
# metrics_df.xs('Total_Maps_Augmented')['Layer'] = len(aug_tracking_rows)
metrics_df.to_csv(os.path.join(out_directory, 'Aug _Metrics.csv'), index=False)

print 'Compiling tracking document'
tracking_df = pd.DataFrame(aug_tracking_rows,
                           columns=['MXD_Name', 'Total_Layers_Added', 'Layers_Added']
                           )
tracking_df.to_csv(os.path.join(out_directory, 'Aug_Tracking_Doc.csv'), index=False)
executionTime = (time.time() - startTime)/3600  # execution time in hours
print 'Time taken to execute script: ' + str(executionTime) + 'h'
print 'DONE!'
