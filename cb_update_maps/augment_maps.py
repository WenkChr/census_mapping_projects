import arcpy
import sys
import os
import arcpy.mapping as mp
import shutil
import pandas as pd
import time

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



def checkForOverlap(df, outGDB, checkLayer):
    # Checks if the layer falls into the map extent and if it does then it is retained if not it is not returned

    def getMapExtentPolygon(df, outGDB, outName='Visible_Extent_Polygon'):
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
        arcpy.CopyFeatures_management(polygon, vis_ext_poly)  # Add the new polygon to the empty feature class

        return vis_ext_poly  # return the extent feature class

    map_extent_polygon = getMapExtentPolygon(df, outGDB)

    arcpy.SelectLayerByLocation_management(checkLayer, 'INTERSECT', map_extent_polygon)
    if int(arcpy.GetCount_management(checkLayer)[0]) > 0:
        arcpy.SelectLayerByAttribute_management(checkLayer, selection_type='CLEAR_SELECTION')
        return True

    arcpy.SelectLayerByAttribute_management(checkLayer, selection_type='CLEAR_SELECTION')
    return False


def addLayerToMDB(mdb, lyr):
    # Adds lyr file to the maps mdb and returns a path to the new fc
    arcpy.FeatureClassToFeatureClass_conversion(lyr, mdb, lyr.name)
    return os.path.join(mdb, lyr.name)


def moveLyr(mapdoc, dataframe, lyr_to_move, reference_lyr_name, keyword='AFTER'):
    '''
    Move layer within a dataframe in relation to the reference layer. The keywork determines whether the layer is
    moved above or below the reference layer
    '''

    move_lyr = mp.ListLayers(mapdoc, lyr_to_move.name, dataframe)[0]
    ref_lyr = mp.ListLayers(mapdoc, reference_lyr_name, dataframe)[0]
    mp.MoveLayer(df, ref_lyr, move_lyr, keyword)


# ----------------------------------------------------------------------------------------------------------------------
# Inputs

# working_directory is where all the unzipped mxd's and mdb's are located
working_directory = 'INPUT PATH TO THE DIRECORY WHERE THE GMS FILES HAVE BEEN EXTRACTED TO'
# out_directory is where the augmented mdb's and mxd's will be placed
out_directory = 'INPUT PATH TO OUTPUT DIRECTORY'
# workingGDB will hold the map extent polygons and any other transitory products

lyr_workspace = 'INPUT PATH TO WHERE WORKING GDB AND SYMBOLOGY LAYER ARE STORED'
workingGDB = os.path.join(lyr_workspace, 'working.gdb')  # WORKING GDB SHOULD BE NAMED working.gdb if not change this

# New CB Style guide
new_cb_lyr = os.path.join(lyr_workspace, 'WC2021CSD_202103_full.lyr') # CAN BE CHANGED IF LYR NME IS DIFFERENT
# Data to augment with
new_cb_fc = os.path.join(workingGDB, 'WC2021CSD_202103_full') # NAME CAN BE CHANGED IF DIFFERENT

new_geom_polys = os.path.join(workingGDB, 'WC2021CSD_202103') # NAME CAN BE CHANGED IF DIFFERENT
new_geom_lines = os.path.join(workingGDB, 'WC2021CSD_202103_lines') # DOES NOT NEED TO EXIST WILL BE CREATED

# ----------------------------------------------------------------------------------------------------------------------
# Logic
# Initial layer setup and prep
startTime = time.time() # capture start time

# Convert fc to layer and add a definition query where necessary
print'Creating new CB lyr file'
cb_fc_lyr = mp.Layer(new_cb_fc)
print 'Creating line file from polygon geometry (if necessary)'
if not arcpy.Exists(new_geom_lines):
    arcpy.PolygonToLine_management(new_geom_polys, new_geom_lines)

metrics = []  # Setup metrics tracking list

# iterate over the mxd's and augment
file_list = list_directory_files(working_directory, '.mxd')
map_count = 0
for f in file_list:

    # if map_count == 10:
    #     break
    #
    # map_count += 1

    metrics_row = []  # Create metrics row
    mxd_name = os.path.split(f)[1]  # Extract mxd name
    metrics_row.append(mxd_name)
    mxd = mp.MapDocument(f)  # open map doc
    df = mp.ListDataFrames(mxd)[0]  # Select the first df as there is only 1 in each map
    # Add layers in new_layers to copied mdb and then create a list of the layers to then add to the map
    # Project the layers so that the sr's match
    sr = df.spatialReference

    print 'Checking to see if new layer falls within map extent'
    line_lyr = mp.Layer(new_geom_lines)
    overlap = checkForOverlap(df, workingGDB, line_lyr)
    metrics_row.append(overlap)
    if overlap is False:
        print 'New geometry does not fall within the map extent. Moving on to next map.'
        metrics.append(metrics_row)
        continue  # If the overlap is false then skip exporting it

    print 'Augmenting map #{} of {}'.format((file_list.index(f)) + 1, len(file_list))
    print 'MXD name: ' + mxd_name

    # Setup new mdb for the mxd add the new layers to this document
    current_mdb_path = os.path.join(os.path.split(f)[0], os.path.split(f)[1].split('.')[0] + '.mdb')
    working_mdb_path = os.path.join(out_directory, os.path.split(current_mdb_path)[1].split('.')[0] + '_CSD202103.mdb')

    if os.path.exists(working_mdb_path): # if the mdb already exists delete it
        os.remove(working_mdb_path)
    working_mdb = shutil.copy(current_mdb_path, working_mdb_path)  # copy the working mdb over into the working folder

    # Setup all other important variables


    print 'Resourcing database for existing layers'
    mxd.replaceWorkspaces(current_mdb_path, 'ACCESS_WORKSPACE', working_mdb_path, 'ACCESS_WORKSPACE')

    template_type = '{}X{}'.format(int(mxd.pageSize.width), int(mxd.pageSize.height))  # indicates the map template wXl

    print 'Adding layer to map mdb and projecting them in the maps projection'

    fc = os.path.join(workingGDB, cb_fc_lyr.name + '_up')  # Convert to unprojected version
    arcpy.FeatureClassToFeatureClass_conversion(cb_fc_lyr, workingGDB, cb_fc_lyr.name + '_up')
    fc_sr = arcpy.Describe(fc).spatialReference
    geo_transformations = arcpy.ListTransformations(fc_sr, sr)
    fc_name = cb_fc_lyr.name  # For getting style guide reference
    prj_fc = os.path.join(working_mdb_path, fc_name)  # Path to projected fc

    if len(geo_transformations) > 0:
        # If there is a geo transformation required use it
        arcpy.Project_management(fc, prj_fc, sr, geo_transformations[0], fc_sr)
    if len(geo_transformations) == 0:
        # If no geo transformation required go ahead and project
        arcpy.Project_management(fc, prj_fc, sr)

    # Add the layers to the map and add to the top until new order decided

    print 'Adding new CB layer to map and applying symbology'
    # Convert to lyr then apply symbology then add to map
    lyr = mp.Layer(new_cb_lyr)
    mp.AddLayer(df, lyr, 'AUTO_ARRANGE')

    # Replace lyr data sources with project mdb's
    mxd.replaceWorkspaces(workingGDB, 'FILEGDB_WORKSPACE', working_mdb_path, 'ACCESS_WORKSPACE')

    moveLyr(mxd, df, lyr, 'csd_al', keyword='AFTER')  # Move the lyr to the correct location the dataframe

    print 'Exporting Map'
    # Required variables
    base_name = os.path.split(f)[1].split('.')[0]
    mxd_out_file = os.path.join(out_directory, '{}_CSD202103.mxd'.format(base_name))  # MXD out path
    # Save files logic
    mxd.saveACopy(mxd_out_file)  # Saves a copy of the augmented map to preserve original
    metrics.append(metrics_row)
    del mxd
    del working_mdb_path

metrics_df = pd.DataFrame(metrics, columns=['MXD_NAME', 'NEW_BOUNDS_IN_EXTENT'])
metrics_df.to_csv(os.path.join(out_directory, 'new_cb_metrics.csv'), index= False)
executionTime = (time.time() - startTime)/3600  # execution time in hours
print 'Time taken to execute script: ' + str(executionTime) + 'h'
print 'DONE!'
