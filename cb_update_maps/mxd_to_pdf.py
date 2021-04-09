import os
import sys
import arcpy
import pandas as pd
from arcpy import mapping as mp

arcpy.env.overwriteOutput = True

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


#-----------------------------------------------------------------------------------
# Inputs

working_directory = 'INPUT PATH TO DIRECTORY CONTAINING AUGMENTED FILES'

metrics_csv = os.path.join(working_directory, 'new_cb_metrics.csv')  # Output path for metrics csv

out_dir = 'INPUT PATH TO PROPERLY STRUCTURED OUTPUT DIRECTORY'

#-----------------------------------------------------------------------------------
# Logic

metrics_df = pd.read_csv(metrics_csv)

metrics_df = metrics_df.loc[metrics_df['NEW_BOUNDS_IN_EXTENT'] == True]  # Take only the mxd's that have the new data

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
                    '62': 'Edmonton'}  # Parses province code into destination city
map_count = 0
for mxd_name in metrics_df['MXD_NAME']:  # Loop over the True MXD's and

    pdf_name = mxd_name.split('.')[0]  # Get the base name for the pdf
    prcode = pdf_name.split('-')[4][:2]  # Determine Province code

    print 'PDFing {}'.format(mxd_name)

    if '_CSD202103.mxd' not in mxd_name:
        mxd_name = mxd_name.split('.')[0] + '_CSD202103.mxd'  # this is here because I made a mistake not adding this to the metrics doc

    mxd_path = os.path.join(working_directory, mxd_name)  # make path to mxd from components
    mxd = mp.MapDocument(mxd_path)  # Make mxd object

    pdf_path = os.path.join(out_dir, destination_dict[prcode], pdf_name + '.pdf')  # Build PDF path
    mp.ExportToPDF(mxd, pdf_path)  # Export map as PDF
    map_count += 1

print 'Total # of maps updated ' + str(map_count)
print 'DONE!'
