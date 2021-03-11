# This script counts crops using multiple ArcGIS tools and a bit of Image Processing.  
# Prerequisites before using this algorithm/script:
# 1. Imagery should be provided by the user. Either it should be RGB imagery or Multispectral. Several Indices can be 
# calculated and exported in local drive bsaed on the imagery type provided
# 2. Shapefile (a polygon line drawn over the crops) should be provided by the user.
# Limitation of this algorithm: Weeds gets counted if they are present in-between the crops
# Original workflow in ArcGIS was developed by Dr. J. Paulo Flores (Assistant Prof. at NDSU)
# Codes were developed by Nitin Rai (PhD Student)
# Agricultural Engineering, Precision Agriculture
# North Dakota State University, USA

# Importing packages
import numpy as np
import arcpy # from ArcGIS 
import os
import sys
from arcpy.ia import * # Image Analyst
from arcpy.sa import * # Spatial Analyst
from arcpy import env 
from arcgis.geoanalytics import manage_data
from arcpy.sa import Raster, Float
import rasterio # Working with Raster Dataset
import gdal # Geospatial Data Abstraction Library
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')
import copy
import csv
import os
import sys

# Reading the imagery (can be .jpg or .png too) from the local HD
RGB_imagery = r"E:/Nitin.Rai/Lab8/output/Sunflowers.tif"
raster = rasterio.open(RGB_imagery)
# counting number of bands within the loaded raster file
arcpy.env.workspace = RGB_imagery
band_count = raster.count
bands = [Raster(os.path.join(RGB_imagery, b))
         for b in arcpy.ListRasters()]
print(band_count)
# User can list all the raster files present within the working directory and print it
#raster_list = arcpy.ListRasters("*")
#print (raster_list)
# Extra information about the raster data loaded
#raster.width
#raster.height
#raster.meta
# Extracting bands from the loaded raster data 
# Setting up the working directory
# print(band_count)
# Another way to open raster file
# Excess = r'C:\Users\nitin.rai\Desktop\ArcGIS Pro\PAG654LABS\Lab7\Lab_Practice\Sunf_ExGr_AOI_Lab7.tif'
# raster_dataset = gdal.Open(Excess)
# env.outputCoordinateSystem = arcpy.SpatialReference("WGS_1984_UTM_Zone_14N")

#################### Additional features in this script/algorithm #############################
###############################################################################################
# Here the operation is dependent on band count. If the band count is equal to 5 then the script assumes it's a 5-band imagery
# and starts calculating all the indices. More indices can be added to the workflow. Whereas, if the band count is greater than
# 5, then an error message is displayed asking user to enter an imagery which is either 3-band or 5-band.
# If the band count is equal equal to 3 or 4, then Excess Green is automatically calculated and stored to the HDD.
# As in array function, the index starts from 0 onwards.
# # For a multispectral imagery (RedEdge MicaSense), 0  = Blue band, 1 = green, 2 = red, 3 = RedEdge, 4 = NIR
if band_count > 5:
    print("Input Imagery should be 3-band RGB Imagery or 5-band Multispectral Imagery")
elif band_count == 5:
    path = os.path.dirname(imagery)
    base1 = os.path.basename(imagery)
    base = os.path.splitext(base1)[0]
    ndvi_filename = base + "_NDVI.tif"
    ndre_filename = base + "_NDRE.tif"
    savi_filename = base + "_SAVI.tif"
    osavi_filename = base + "_OSAVI.tif"
    arcpy.env.workspace = imagery
    ndvi = (Float(bands[4]) - bands[2]) / (Float(bands[4]) + bands[2]) 
    ndvi.save(ndvi_filename)
    print ("NDVI successfully calculated")
    ndre = (Float(bands[4]) - bands[3]) / (Float(bands[4]) + bands[3]) 
    ndre.save(ndre_filename)
    print ("NDRE successfully calculated")
    savi = 1.5 * ((Float(bands[4]) - bands[2]) / (Float(bands[4]) + bands[2] + 0.5))
    savi.save(savi_filename)
    print ("SAVI successfully calculated")
    osavi = 1.16 * ((Float(bands[4]) - bands[2]) / (Float(bands[4]) + bands[2] + 0.16))
    osavi.save(osavi_filename)
    print ("OSAVI successfully calculated")
else:
    path = os.path.dirname(RGB_imagery)
    base1 = os.path.basename(RGB_imagery)
    base = os.path.splitext(base1)[0]
    ExGreen_filename = base + "_ExcessGreen.tif"
    # Band Normalization
    total_bands = (Float(bands[0] + bands[1] + bands[2]))
    red_band = (Float(bands[2]) / total_bands)
    green_band = (Float(bands[1]) / total_bands)
    blue_band = (Float(bands[0]) / total_bands)
    ExGreen = (2 * green_band - red_band - blue_band)
    ExGreen.save(ExGreen_filename)
    arcpy.env.workspace = path
    print ("You have successfully exported the Excess Green.tif file")
    arcpy.BuildPyramids_management(ExGreen_filename, "", "NONE", "BILINEAR","", "", "")
    print ("Excess Green pyramids successfully calculated")

# Sharpening the image so the objects (crops & weeds) details are highlighted
sharpen_ExGreen = arcpy.ia.Convolution(ExGreen, 20)
sharpen_ExGreen.save(r'E:/Nitin.Rai/Lab8/output/ExGreen_Sharpened.tif')
print("You have successfully sharpened the Excess Green.tif file!")
arcpy.BuildPyramids_management(sharpen_ExGreen, "", "NONE", "BILINEAR","", "", "")

# Converting the above sharpened image into binary image, thresholding technique is applied here 
# converting the imagery into 0 and 1.
binary_raster = arcpy.ia.Threshold(sharpen_ExGreen)
binary_raster.save(r"E:/Nitin.Rai/Lab8/output/ThresholdSharpen.tif")
print("You have successfully perfromed Imagery Thresholding!")

# Converting Raster to Polygon (a shapefile is generated for the whole raster file)
# objects within the raster file is 1s while all the rest is 0s
arcpy.env.workspace = 'E:/Nitin.Rai/Lab8/Dataset/Dataset'
inRaster = "ThresholdSharpen.tif"
outPolygons = r"E:/Nitin.Rai/Lab8/output/RasterToPolygonConvert.shp"
field = "VALUE"
arcpy.RasterToPolygon_conversion(inRaster, outPolygons, "NO_SIMPLIFY", field)
print("You have successfully converted Raster to Polygon!")

# Selecting all the 1s so that we can export a shapefile for all the objects labeled 1s within the imagery
arcpy.env.workspace = r'E:/Nitin.Rai/Lab8/output'
polygonAttached = "RasterToPolygonConvert.shp"
selectedAttributes = arcpy.SelectLayerByAttribute_management(polygonAttached, "NEW_SELECTION", '"gridcode" > 0')
arcpy.CopyFeatures_management(selectedAttributes, 'Attributes_SelectedGridOne')

# At this step, user provides a line shpaefile denoting crop rows.
arcpy.env.workspace = r'E:/Nitin.Rai/Lab8/output'
cropsline = "PAG454_AOI_S21_Sunf_Rows.shp"
rowsBuffered = r'E:/Nitin.Rai/Lab8/output/ROI_Buffered2Inches'
# Specifying buffer of 3 inches using the line shapefile provided by the user
distanceField = "2 Inches"
sideType = "FULL"
endType = "FLAT"
dissolve = "NONE"
# Finally storing the buffer shapefile in Buffered_CropsLine
Buffered_CropsLine = arcpy.Buffer_analysis(cropsline, rowsBuffered, distanceField, sideType, endType, dissolve)

# At this step we are going to intersect buffered rows with polygon we created while converting raster to polygon
arcpy.env.workspace = r'E:/Nitin.Rai/Lab8/output'
BufferFeature = ["ROI_Buffered2Inches.shp", "RasterToPolygonConvert.shp"]
OutputIntersect = r'E:/Nitin.Rai/Lab8/output/IntersectBufferedPolygons.shp'
join_attributes = "ALL"
arcpy.Intersect_analysis(BufferFeature, OutputIntersect, join_attributes, "", "INPUT")

# At this step we are going to dissolve buffered rows with polygon we created in the last step
arcpy.env.workspace = r'E:/Nitin.Rai/Lab8/output'
dissolve_features = "IntersectBufferedPolygons.shp"
output_dissolve = r'E:/Nitin.Rai/Lab8/output/RandomOutputAccept.shp'
dissolve_field = "Row_ID"
statitics_field = [["Id", "Count"]]
multi_features = "MULTI_PART"
arcpy.Dissolve_management(dissolve_features, output_dissolve, dissolve_field, statitics_field, 
                                multi_features, "")

arcpy.env.workspace = r'E:/Nitin.Rai/Lab8/output'
in_table = r'E:/Nitin.Rai/Lab8/output/randomcounts/RandomOutputAccept.dbf'
out_path = r'E:/Nitin.Rai/Lab8/output/randomcounts'
out_csv = "cropcountsExcel.csv"
# in_delimiter = "COMMA"
arcpy.TableToTable_conversion(in_table, out_path, out_csv, "", "", "")
