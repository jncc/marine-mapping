########################################################################################################################

# Title: Combined Map Updates

# Authors: Matear, L.(2019)
# Version Control: 1.0

# Script description:    The following Python code has been developed for use within the ESRI ArcGIS Python Console,
#                        therefore, this will not execute successfully from a standard Python IDE.
#
#
#                        To ensure no permanent alterations are made to the master documents, all data used within this
#                        script are copies of the original files. Files referenced within this code have been copied to
#                        a local location (D:) to reduce overall processing speed.
#
#                        For any enquiries please contact Liam Matear by email: Liam.Matear@jncc.gov.uk

########################################################################################################################

#                                                      CONTENTS                                                        #

########################################################################################################################

# PLEASE NOTE: Subsections are not listed, but can be found under each relevant area of the code

# 1. UPDATING THE COMBINED MAP WITH UKSeaMap
# 1.1. Readying UKSeaMap
# 1.2. Inserting UKSeaMap from the combined map

# 2. REMOVING NE EVIDENCE BASE FROM THE COMBINED MAP
# 2.1. Removing NE_Ev_2 and NE_Evid data

# 3. UPDATING THE COMBINED MAP WITH NEW SURVEY DATA
# 3.1. Identifying new maps to add
# 3.2. Adding the new EUNIS Reference maps into the combined map
# 3.3. Creating a control data frame
# 3.4. Importing confidence metadata (3-step and MESH) / incl. metadata checks
# 3.5. Creating metadata for all new survey maps to be added into the combined map
# 3.6. Creating metadata for the intersected existing maps
# 3.7. Run the 5 stage decision tree analysis on the existing and new maps - comparing new and existing data
# 3.8. Joining decision results to geospatial data
# 3.9. Readying the intersected new survey / combined map data for overwriting

# 4. REINSERTING THE NE EVIDENCE BASE INTO THE COMBINED MAP

########################################################################################################################

# Initial setup and setting of arcpy workspace

# Import all Python libraries required within ArcPy
import arcpy
from arcpy import env

# Import all Python libraries required for IDE execution
import os
import pandas as pd
import ast

########################################################################################################################

#                                    1. UPDATING THE COMBINED MAP WITH UKSeaMap                                        #

########################################################################################################################

# 1.1. Readying UKSeaMap

# 1.1.1. Ensuring that UKSeaMap is in the EMODnet Seabed Habitats Translated Habitat DEF data structure

# 1.1.2. Correctly completing field entries
#        If the data does not have this structure, use the following code below to populate the data with the required
#        fields

##########################
# [THIS SECTION IS WRITTEN IN ARCPY AND CAN ONLY BE EXECUTED FROM ESRI ArcGIS PYTHON CONSOLE]
##########################

#   Adds correctly formatted TRANSLATED HABITAT DEF mandatory fields to ESRI Shapefiles or geodatabase featureclasses
#   Enter folder (or geodatabase/dataset) containing the input shapefiles in the command prompt
#   Script will check for mandatory fields and add if necessary.
#   IMPORTANT: This script will NOT delete fields, this must be done manually once field data input is complete

#   Created by: Graeme Duncan, JNCC for EMODnet Seabed Habitats 2014.
#   Contact: info@emodnet-seabedhabitats.eu
##########################


root_workspace = raw_input('Paste the full directory path to the folder containing your habitat maps here: ')
arcpy.env.workspace = root_workspace
newlist = arcpy.ListFeatureClasses()

##########################


add_fields = [
     ("GUI", "TEXT", "#", "#", 8),
     ("POLYGON", "LONG", 8, "#", "#"),
     ("ORIG_HAB", "TEXT", "#", "#", 254),
     ("ORIG_CLASS", "TEXT", "#", "#", 254),
     ("HAB_TYPE", "TEXT", "#", "#", 20),
     ("VERSION", "TEXT", "#", "#", 50),
     ("DET_MTHD", "TEXT", "#", "#", 254),
     ("DET_NAME", "TEXT", "#", "#", 254),
     ("DET_DATE", "DATE", "#", "#", "#"),
     ("TRAN_COM", "TEXT", "#", "#", 254),
     ("T_RELATE", "TEXT", "#", "#", 1),
     ("VAL_COMM", "TEXT", "#", "#", 254)]

for fc in newlist:
    # Add all fields
    print("Adding fields to " + str(fc) + " ...")
    field_name_list = [field.name for field in arcpy.ListFields(fc) if not (field.type in ["OID", "Geometry"] or field.name in ["Shape_Length", "Shape_Area"])]
    for fieldToAdd in add_fields:
        if fieldToAdd[0] not in field_name_list:
            print("Adding field " + str(fieldToAdd[0]) + " to " + str(fc) + " ")
            try:
                arcpy.AddField_management(fc, fieldToAdd[0], fieldToAdd[1], fieldToAdd[2], fieldToAdd[3], fieldToAdd[4])
            except Exception as e:
                print("Error ading field '%s' to %s" % (str(fieldToAdd[0]), str(fc)))
                print(e.message)
            else:
                print("Field successfully added")
        else:
            print("Field '%s' already exists in %s, ignoring..." % (str(fieldToAdd[0]), str(fc)))
    print("______________________")

raw_input('Process complete, press enter to quit')


# 1.1.3. Creating a EUNIS L3 Attribute Field
#        In a copy of the dataset, create a new field “E_L3_LON” which is a text/string type of length 10.
arcpy.AddField_management("Insert target feature here", "Insert field name here", "TEXT", "", "", 10, "", "", "REQUIRED", "")

# 1.1.4. Completing EUNIS level 3 values for each polygon in the above field
#  	     This can be done manually if you want just by selecting by EUNIS values and batch-filling with the relevant
#  	     level 3 value. Alternatively, this can be automated using the body of code below developed by G. Duncan (2016).

# Use formula "eunisToAllLevel3(!HAB_TYPE!)" in field calculator (Python of course) with the below as the code block.
# Warning: This will only pull out TRUE eunis habitats from the input field.
#          Therefore, any places where the input is a non-eunis value (e.g.
#          "deep sea coarse sediment" or "deep sea seabed") will have to be
#          manually added later (e.g. to "A6" in those cases).
# Therefore:
# POST-SCRIPT-RUN - check for all "Void" values in the output field to test if
#                  they can be manually attributed a level 3 or 2 habitat.

import re

# Suggest keeping at False to standardise the concatenation, but can change to True to use the function below.
# If set "y", uses the first matching concatenator in original hab_type field
useConcatenateBool = False
# What to use as concatenator if you're not getting it from the original field (i.e. above is set to False) or if
# nothing matches in original.
concatenatorDefault = '+'
# Are L2 habitats to be removed from the output? True/False
removeL2Bool = True
# Are there any habitats that would be caught by the above that should be retained (e.g. deep sea "A6")
keepList = ['A6']
# Should the output list be alphabetised for standardisation? True/False
sortListBool = True


eunisPattern = re.compile(r'(\b(?:[ABCJ](?:[0-9](?:\.[0-9]*)?))|\b[ABCJ]\b)')
concatenatePattern = re.compile(r'([\\/+\&]|or)')


# Tries to use the (first instance of a) habitat concatenator to output into the final result.
# If no matches found, defaults to "+"
# Potential matches are "\" "/" "+" and "&"
def collectConcatenator(searchString):
    concatenateMatches = re.search(concatenatePattern, searchString)
    if concatenateMatches:
        return concatenateMatches.group(0)
    else:
        return '+'


def eunisToAllLevel3(eunisFull):
    if useConcatenateBool:
        concatenator = collectConcatenator(eunisFull)
    else:
        concatenator = concatenatorDefault
    eunisMatches = re.findall(eunisPattern, eunisFull)
    habFirstFour = set([x[:4] for x in eunisMatches])
    if removeL2Bool:
        habFirstFour = [x for x in habFirstFour if ((len(x) > 3) or x in keepList)]
    if sortListBool:
        habFirstFour = sorted(habFirstFour)
    if len(habFirstFour) == 0:
        return 'Void'
    else:
        return concatenator.join(habFirstFour)


#        Set the Field Calculator to use Python rather than VB, Paste the contents of the above into the 'Codeblock'
#        section, and then call the function in the main Field Calculator window with HAB_TYPE field as the input value
#        e.g. eunisToAllLevel3(!HAB_TYPE!)

# 1.1.5. Check the data for any geometry errors and overlaps.

########################################################################################################################

# 1.2. Inserting UKSeaMap from the combined map

##########################
# [THIS SECTION IS WRITTEN IN ARCPY AND CAN ONLY BE EXECUTED FROM ESRI ArcGIS PYTHON CONSOLE]
##########################

# 1.2.1. 'Reverse select' all data within combined map which is not UKSM 2016 data
#         Export this selection within the Geodatabase as a featureclass “Combined_extract”.
arcpy.SelectLayerByAttribute_management("Enter combined map here", "SWITCH_SELECTION", "[GUI] = 'UKSM16'")

# 1.2.2. Select by location on UKSeaMap where it intersects with the Combined_extract output
#        Export this selection as “UKSM_intersecting” in your working Geodatabase.
arcpy.SelectLayerByLocation_management("Enter UKSeaMap here", "Combined_extract", "INTERSECT")

#        Reverse the selection - export this selection as “UKSM_notintersecting” in your working Geodatabase.
arcpy.SelectLayerByLocation_management("Enter UKSeaMap here", "Combined_extract", "INTERSECT", "INVERT")

#        Use the “Erase” tool, with 'UKSM_intersecting' as your input features, and the output of Combined_extract
#        Save the output as “UKSM_erased” - this may take a while, can leave overnight
arcpy.Erase_analysis("UKSM_intersecting", "Combined_extract", "Insert output gdb filepath here", "#")

# 1.2.3. Merge UKSM_erased and UKSM_notintersecting together and clip data by UK Mean High Water polygon.
#        Save the output as UKSM_erased_intersecting_merge
arcpy.Merge_management("UKSM_erased;UKSM_notintersecting", "Insert output gdb filepath here")

#        Reverse the selection in ArcGIS from the UK MHW polygon and export as 'mhw_land'
#        Re-project 'mhw_land' to wgs_84 to minimise errors
#        Save as mhw_land_wgs84
arcpy.Project_management("mhw_land", "Insert output gdb filepath here", "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433],METADATA['World',-180.0,-90.0,180.0,90.0,0.0,0.0174532925199433,0.0,1262]]","ED_1950_To_WGS_1984_18","PROJCS['Europe_Albers_Equal_Area_Conic_MPACal',GEOGCS['GCS_European_1950',DATUM['D_European_1950',SPHEROID['International_1924',6378388.0,297.0]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Albers'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',10.0],PARAMETER['Standard_Parallel_1',50.2],PARAMETER['Standard_Parallel_2',61.2],PARAMETER['Latitude_Of_Origin',30.0],UNIT['Meter',1.0]]")

#        Erase the UKSM_erased_intersecting_merge by mhw_land_wgs84 to remove any landward erroneous data
#        Save as 'UKSM_merge_land_erase'
arcpy.Erase_analysis("UKSM_erased_intersecting_merge", "mhw_land_wgs84", "Insert output gdb filepath here", "#")

#        Create copy of the combined extract feature within the geodatabase - save as 'Combined_insert'
arcpy.FeatureClassToGeodatabase_conversion(["Combined_extract"], 'Insert output gdb filepath here')

# 1.2.4. Finally, append (No test option) 'UKSM_merge_land_erase' into Combined_Insert data
arcpy.Append_management("UKSM_merge_land_erase", "Combined_insert2", "NO_TEST", """POLYGON "POLYGON" true true false 4 Long 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,POLYGON,-1,-1;GUI "GUI" true true false 8 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,GUI,-1,-1;ORIG_HAB "ORIG_HAB" true true false 254 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,ORIG_HAB,-1,-1;HAB_TYPE "HAB_TYPE" true true false 20 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,HAB_TYPE,-1,-1;VERSION "VERSION" true true false 50 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,VERSION,-1,-1;DET_MTHD "DET_MTHD" true true false 500 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,DET_MTHD,-1,-1;DET_NAME "DET_NAME" true true false 254 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,DET_NAME,-1,-1;DET_DATE "DET_DATE" true true false 8 Date 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,DET_DATE,-1,-1;TRAN_COM "TRAN_COM" true true false 500 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,TRAN_COM,-1,-1;T_RELATE "T_RELATE" true true false 1 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,T_RELATE,-1,-1;VAL_COMM "VAL_COMM" true true false 500 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,VAL_COMM,-1,-1;EUNIS_L3 "EUNIS_L3" true true false 10 Text 0 0 ,First,#;HAB_TYPE04 "HAB_TYPE04" true true false 20 Text 0 0 ,First,#;ORIG_CLASS "ORIG_CLASS" true true false 254 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,ORIG_CLASS,-1,-1;AreaKm2 "AreaKm2" true true false 8 Double 0 0 ,First,#;Shape_Leng "Shape_Leng" true true false 8 Double 0 0 ,First,#;MCZ_Dataset_UID "MCZ_Dataset_UID" true true false 50 Text 0 0 ,First,#;MCZ_MM_Source_ID "MCZ_MM_Source_ID" true true false 50 Text 0 0 ,First,#;MCZ_Date "MCZ_Date" true true false 8 Date 0 0 ,First,#;MCZ_IsBSH "MCZ_IsBSH" true true false 10 Text 0 0 ,First,#;MCZ_IsHOCI "MCZ_IsHOCI" true true false 10 Text 0 0 ,First,#;MCZ_Eunis_L3 "MCZ_Eunis_L3" true true false 32 Text 0 0 ,First,#;MCZ_Eunis_L2 "MCZ_Eunis_L2" true true false 10 Text 0 0 ,First,#;MCZ_HOCI_name "MCZ_HOCI_name" true true false 128 Text 0 0 ,First,#;MCZ_Source_dataset "MCZ_Source_dataset" true true false 256 Text 0 0 ,First,#;MCZ_Source_ID "MCZ_Source_ID" true true false 50 Text 0 0 ,First,#;MCZ_Source_ID_MESH "MCZ_Source_ID_MESH" true true false 50 Text 0 0 ,First,#;MCZ_MESH_confidence_score "MCZ_MESH_confidence_score" true true false 4 Float 0 0 ,First,#;MCZ_UID_BSH "MCZ_UID_BSH" true true false 254 Text 0 0 ,First,#;MCZ_UID_FOCI "MCZ_UID_FOCI" true true false 254 Text 0 0 ,First,#;Source "Source" true true false 10 Text 0 0 ,First,#;Shape_Length_1 "Shape_Length" true true false 8 Double 0 0 ,First,#;Shape_Area_1 "Shape_Area" true true false 8 Double 0 0 ,First,#;HAB_LONG "HAB_LONG" true true false 50 Text 0 0 ,First,#;grid_code "grid_code" true true false 4 Long 0 0 ,First,#;ModelCod "ModelCod" true true false 4 Long 0 0 ,First,#;EUNIScom "EUNIScom" true true false 254 Text 0 0 ,First,#;AllcombD "AllcombD" true true false 254 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,AllcombD,-1,-1;Grouped "Grouped" true true false 254 Text 0 0 ,First,#;E_L3_LON "E_L3_LON" true true false 50 Text 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,E_L3_LON,-1,-1;NCOllieHabPoly20160125_grid_code "grid_code" true true false 4 Long 0 0 ,First,#;HabsLayerTable_csv_OID_ "csv.OID_" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_Value "csv.Value" true true false 4 Long 0 0 ,First,#;HabsLayerTable_csv_Count "csv.Count" true true false 4 Long 0 0 ,First,#;HabsLayerTable_csv_Enecode "csv.Enecode" true true false 4 Long 0 0 ,First,#;HabsLayerTable_csv_Combined_energy "csv.Combined energy" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_BioZCode "csv.BioZCode" true true false 4 Long 0 0 ,First,#;HabsLayerTable_csv_biozone "csv.biozone" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_BioZGroup "csv.BioZGroup" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_SubtCode "csv.SubtCode" true true false 4 Long 0 0 ,First,#;HabsLayerTable_csv_Substrate "csv.Substrate" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_SubsGroups "csv.SubsGroups" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_SubsGrpPlu "csv.SubsGrpPlu" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_ModelCode "csv.ModelCode" true true false 4 Long 0 0 ,First,#;HabsLayerTable_csv_EUNIScomb "csv.EUNIScomb" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_EUNIScombD "csv.EUNIScombD" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_Allcomb "csv.Allcomb" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_Allcombdes "csv.Allcombdes" true true false 255 Text 0 0 ,First,#;HabsLayerTable_csv_Grouped "csv.Grouped" true true false 255 Text 0 0 ,First,#;ORIG_FID "ORIG_FID" true true false 4 Long 0 0 ,First,#;MCZ_Date_year "MCZ_Date_year" true true false 2 Short 0 0 ,First,#;MCZ_IsSOCI "MCZ_IsSOCI" true true false 10 Text 0 0 ,First,#;MCZ_IsMobileSpecies "MCZ_IsMobileSpecies" true true false 10 Text 0 0 ,First,#;MCZ_SOCI_name "MCZ_SOCI_name" true true false 128 Text 0 0 ,First,#;MCZ_Original_survey "MCZ_Original_survey" true true false 256 Text 0 0 ,First,#;MCZ_Source_ID_MR "MCZ_Source_ID_MR" true true false 50 Text 0 0 ,First,#;MCZ_Additional_information "MCZ_Additional_information" true true false 1000 Text 0 0 ,First,#;MCZ_Use_feature "MCZ_Use_feature" true true false 10 Text 0 0 ,First,#;MCZ_MobileSpecies_name "MCZ_MobileSpecies_name" true true false 128 Text 0 0 ,First,#;MCZ_Feature_code "MCZ_Feature_code" true true false 20 Text 0 0 ,First,#;MCZ_Survey_quality "MCZ_Survey_quality" true true false 2 Short 0 0 ,First,#;SAC_Name "SAC_Name" true true false 120 Text 0 0 ,First,#;SAC_Code "SAC_Code" true true false 12 Text 0 0 ,First,#;SAC_SFCODE "SAC_SFCODE" true true false 254 Text 0 0 ,First,#;SAC_UID "SAC_UID" true true false 50 Text 0 0 ,First,#;SPA_Name "SPA_Name" true true false 120 Text 0 0 ,First,#;SPA_Code "SPA_Code" true true false 12 Text 0 0 ,First,#;SPA_SFCODE "SPA_SFCODE" true true false 254 Text 0 0 ,First,#;SPA_UID "SPA_UID" true true false 50 Text 0 0 ,First,#;Ramsar_Name "Ramsar_Name" true true false 120 Text 0 0 ,First,#;Ramsar_Code "Ramsar_Code" true true false 12 Text 0 0 ,First,#;Ramsar_SFCODE "Ramsar_SFCODE" true true false 254 Text 0 0 ,First,#;Ramsar_UID "Ramsar_UID" true true false 50 Text 0 0 ,First,#;MCZ_Name "MCZ_Name" true true false 254 Text 0 0 ,First,#;MCZ_Code "MCZ_Code" true true false 12 Text 0 0 ,First,#;BSH_CODE "BSH_CODE" true true false 6 Text 0 0 ,First,#;Draft "Draft" true true false 3 Text 0 0 ,First,#;Restricted "Restricted" true true false 3 Text 0 0 ,First,#;BiotopeL4 "BiotopeL4" true true false 250 Text 0 0 ,First,#;SummaryBio "SummaryBio" true true false 100 Text 0 0 ,First,#;Shape_Length "Shape_Length" false true true 8 Double 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0 ,First,#,J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/UKSM_merge_land_erase,Shape_Area,-1,-1""","#")

#        Congratulations, you have added UKSM18 into the combined map! High five!


########################################################################################################################

#                                   2. REMOVING NE EVIDENCE BASE FROM THE COMBINED MAP                                 #

########################################################################################################################

#    Prior to updating the combined map with any new survey data, all data from the Natural England (NE) Evidence Base
#    must be removed. Traditionally, overlapping maps would be compared against each other using the decision tree
#    analysis. However, this was deemed erroneous due to discrepancies within confidence assessments completed with
#    varying methodologies. Therefore, to avoid inaccurate comparisons, it was decided that the NE data should be
#    removed at this stage and is subsequently reinserted on top of any survey data which is added into the
#    combined map.


##########################
# [THIS SECTION IS WRITTEN IN ArcPy AND CAN ONLY BE EXECUTED FROM ESRI ArcGIS PYTHON CONSOLE]
##########################

# 2.1. Removing NE_Ev_2 and NE_Evid data

#      Erroneous 'Source' data from the NE_Ev_2 stored as 'NULL' are required to be corrected. This is only needed to be
#      completed once, therefore, this code is not required when generally completing updates to the combined map.
arcpy.CalculateField_management("combinedmap_UKSM18_updated", "Source", "'NE_Ev_2'", "PYTHON", "#")

# 2.1.1. Reverse select all data within the combined map which does not include data from either NE_Ev_2 or NE_Evid
#        sources. The input to this must be the combined map which has been updated with the new UKSM data.
#        Export this selection as 'Combined_map_no_evidbase'
#        NOTE: 'SWITCH_SELECTION' DOES NOT WORK CANNOT RUN SIMULTANEOUSLY WITH SELECT BY ATTRIBUTE
arcpy.SelectLayerByAttribute_management("combinedmap_UKSM18_updated", "NEW_SELECTION", "Source IN ('NE_Ev_2', 'NE_Evid', 'UKSM18'))")
arcpy.SelectLayerByAttribute_management("combinedmap_UKSM18_updated", "SWITCH_SELECTION", "Source IN ('NE_Ev_2', 'NE_Evid', 'UKSM18')")

#        The following code can be run if the user is sure that there are no NULL values within the SOURCE field
arcpy.SelectLayerByAttribute_management("combinedmap_UKSM18_updated", "NEW_SELECTION", "Source NOT IN ('NE_Ev_2', 'NE_Evid', 'UKSM18')")


#        The 'Combined_map_no_evidbase' feature is required to update the combined map with new survey data

########################################################################################################################

#                                 3. UPDATING THE COMBINED MAP WITH NEW SURVEY DATA                                    #

########################################################################################################################

# 3.1. Identifying new maps to add

# 3.1.1. Load the following function into the ArcGIS Geoprocessing Python Console - developed by G.Duncan (2017)

##########################
# [THIS SECTION IS WRITTEN IN ArcPy AND CAN ONLY BE EXECUTED FROM ESRI ArcGIS PYTHON CONSOLE]
##########################

#        Identifying new maps to be added to the combined map

#        Set arcpy.env.workspace to most recent combined map geodatabase
arcpy.env.workspace = r"J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\InputData\working_geodatabase.gdb"


#        Define listUniqueValues() function
#        Function title: listUniqueValues()
def listUniqueValues(inLayer, inField, lineString=False):
    import arcpy
    uniqueSet = set([])
    with arcpy.da.SearchCursor(inLayer, inField) as cursor:
        for row in cursor:
            uniqueSet.add(row[0])
    if lineString:
        output = "\n".join([str(x) for x in uniqueSet])
        return output
    else:
        return (list(uniqueSet))


# 3.1.2. Execute listUniqueValues() function on the combined map layer and GUI field within the layer attributes. This
#        allows the user to search the reference data for maps which are not currently within the combined map
combined_list = listUniqueValues("Insert combined map here", "GUI")
combined_list = listUniqueValues("Combined_map_no_evidbase2", "GUI")

# 3.1.3. Set arcpy.env.workspace to EUNIS reference geodatabase
arcpy.env.workspace = r"J:\Reference\Marine\Habitats\1_EUNIS_HabitatMaps.gdb"

#        Execute previously defined arcpy.listFeatureClasses() function on the combined map layer and GUI field within
#        the layer attributes
reference_list = arcpy.ListFeatureClasses(feature_dataset="Public")

# 3.1.4. Turn newly created combined_list into a set data type
combined_set = set(combined_list)

# 3.1.5. Turn newly created reference_list into a set data type
reference_set = set(reference_list)

# 3.1.6. Search the reference_set for maps which exist within the EUNIS reference data, but are not present in the
#        combined map
new_maps_set = reference_set - combined_set

# 3.1.7. Review new maps which are yet to be included within the combined map
#        Look at the outputs of new_maps_set and, if it isn’t empty, see if the identified maps are definitely to be
#        added or if they’re old and shouldn't be
print(new_maps_set)


########################################################################################################################

# 3.2. Adding the new EUNIS Reference maps into the combined map
#      (If there are any)

##########################
# [THIS SECTION IS WRITTEN IN ARCPY AND CAN ONLY BE EXECUTED FROM ESRI ArcGIS PYTHON CONSOLE]
##########################

# 3.2.1. Create a new working geodatabase within D: drive
arcpy.CreateFileGDB_management(r"Insert your file path here\CombinedMapUpdates", "Insert your working gdb here")

#        Set arcpy.env.workspace to EUNIS reference geodatabase
arcpy.env.workspace = r"J:\Reference\Marine\Habitats\1_EUNIS_HabitatMaps.gdb"

# 3.2.2. Create new geodatabase feature class which is a merge of all new map geodatabase features
#        This list is acquired from new_maps_set in Section 7 above.

# NOTE TO LIAM - GB001336 REMOVED FROM FIRST RUN OUTPUT - SINCE CORRECTED
arcpy.Merge_management([u'GB001117', u'GB000229', u'GB000228', u'GB000227', u'GB000226', u'GB000225', u'GB100013',
                        u'GB000588', u'GB001104', u'GB001106', u'GB001103', u'GB000457', u'GB200015', u'GB100023',
                        u'GB100021', u'GB003002', u'GB003003', u'GB003001', u'GB003006', u'GB001071', u'GB001300',
                        u'GB200001', u'GB100035', u'GB100034', u'GB000283', u'GB000282', u'GB400008', u'GB000235',
                        u'GB400002', u'GB400001', u'GB400007', u'GB400006', u'GB000470', u'GB000312', u'GB000372',
                        u'GB000377', u'GB000338', u'GB100206', u'GB100207', u'GB100204', u'GB100205', u'GB100202',
                        u'GB100203', u'GB001312', u'GB100201', u'GB100208', u'GB100209', u'GB000943', u'GB001089',
                        u'GB100046', u'GB000308', u'GB100200', u'GB100211', u'GB100210', u'GB100213', u'GB000307',
                        u'GB100215', u'GB100214', u'GB001494', u'GB100111', u'GB001092', u'GB001090', u'GB000319',
                        u'GB001333', u'GB000315', u'GB100267', u'GB001144', u'GB000653', u'GB001546', u'GB000654',
                        u'GB100102', u'GB100069', u'GB000443', u'GB000329', u'GB001038', u'GB100072', u'GB000316',
                        u'GB000335', u'GB000334', u'GB000330', u'GB000333', u'GB000234', u'GB100085', u'GB000236',
                        u'GB000230', u'GB000231', u'GB000233', u'GB001214', u'GB100004', u'GB100001', u'GB100002',
                        u'GB100003', u'GB001520'], r"J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\InputData\working_geodatabase.gdb\new_merged_maps3")

# 3.2.3. Copy the combined map into the geodatabase
#        Import a copy of the combined map into the newly created working geodatabase
arcpy.env.workspace = "Insert combined map gdb here"

#        Create target geodatabase for all features to be written to
outputGDB = "Insert target working gdb here"

#        Loop through all data sets and features within the geodatabase with arcpy.da.Walk()
for gdb, datasets, features in arcpy.da.Walk(arcpy.env.workspace):
        for feature in features:
            # For all features within target location, copy and write to the outputGDB
            arcpy.CopyFeatures_management(feature, os.path.join(outputGDB, "Polyline_" + feature))

# 3.2.4. Dissolve all newly merged map features by GUI and save within the working geodatabase as 'new_maps_dissolved'
arcpy.Dissolve_management("Insert filepath to input gdb and feature here", "Insert output file path here \\new_maps_dissolved", "GUI", "#", "MULTI_PART", "DISSOLVE_LINES")

# 3.2.5. Intersect new_maps_dissolved with current combined map
#        Set parameters for intersection analysis
new_maps_dissolved = "Insert new_maps_dissolved gdb filepath here"
combined_map = "Insert copmbined map gdb file path here"
try:
    # Define input data as list
    inputs = [new_maps_dissolved, combined_map]
    # Set output variable name
    output = "Insert output gdb file path here/new_maps_dissoved_combinedmap_intersect"
    # Perform intersection
    arcpy.Intersect_analysis(inputs, output, "ALL", "", "INPUT")

except Exception as e:
    # If error occurs, print line and error message
    import traceback
    import sys
    trace = sys.exc_info()[2]
    print("Line %i" % trace.tb_lineno)
    print(e.message)

# 3.2.6. For each overlapping GUI, work out which map should “win” using the method described in the “5-Stage decision
#        tree” at http://jncc.defra.gov.uk/pdf/20140311_InformationSheet_combinedEUNISL3map_v1.pdf

#        Export data attributes as single excel file
in_table = "D:\\CombinedMapUpdates2018\\working_geodatabase.gdb\\intersection"
out_xls = "D:\\CombinedMapUpdates2018\\intersection_attributes.xls"

#        Execute TableToExcel
arcpy.TableToExcel_conversion(in_table, out_xls)


########################################################################################################################

# 3.3. Creating a control data frame
#      This will provide the information base required to complete the decision tree analyses.

##########################
# [THIS SECTION IS WRITTEN IN PYTHON AND SHOULD BE EXECUTED FROM A CONSOLE / IDE]
##########################

# 3.3.1. Creating a control data frame (df) and data required for to complete the decision tree analysis

#        Import the attributes of the data intersected in Section 6. above to a Pandas DataFrame
Intersection_Attributes = \
    pd.read_csv(r"J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\InputData\Intersection_Attributes_30012019.csv",
                low_memory=False)

#        Group the attributes by existing maps within the Combined Map and all intersections with new data
Intersected_Maps = Intersection_Attributes.groupby(['GUI'])['GUI_1'].apply(list)

#        Convert the Pandas Series Object into a DataFrame to be manipulated later in the script
Intersected_Maps = pd.DataFrame(Intersected_Maps)

#        Reset index of newly created DataFrame to pull data into correctly formatted columns
Intersected_Maps = Intersected_Maps.reset_index(inplace=False)

#        Reset columns within Intersected_Maps DataFrame to reflect newly combined data
Intersected_Maps.columns = ['CombinedMap_GUI', 'NewMap_GUI']

# 3.3.2. Formatting data - removing unwanted 'nan' values

#        Define remove_my_nan() function to remove all unwanted not a number values within the targeted column
def remove_my_nan(df, column):
    """
    Function Title: remove_my_nan()
    Define function to remove all nan values from the HAB_TYPE column of the aggregated DataFrame
    """
    habitat = df[column]
    # Return data as clean habitat if the string value of the habitat is not a 'nan' value
    clean_habitat = [habitat for habitat in habitat if str(habitat) != 'nan']
    return clean_habitat


#        Remove any 'nan' (not a number) values from the Intersected_Maps DataFrame
Intersected_Maps['NewMap_GUI'] = Intersected_Maps.apply(lambda df: remove_my_nan(df, 'NewMap_GUI'), axis=1)


# 3.3.3. Removing duplicate data entries within GUI fields
#        Define list_set() function to convert values within new maps lists into list type
def list_set(x):
    """
    Function Title: list_set()
    Define function to return a list of a set of the original list (basically remove duplicates and return as new
    list)
    """
    return list(set(x))


#        Apply the list_set() function on the list of all new GUIs
Intersected_Maps['NewMap_GUI'] = Intersected_Maps['NewMap_GUI'].apply(list_set)

#        Create control DataFrame for decision tree analysis which only includes the desired Intersection_Attributes
#        fields
Control_DF = Intersection_Attributes[['GUI_1', 'GUI']]

#        Drop duplicate data from Control_DF GUI fields
#        This will create a df which will list all unique intersections between new and existing data
Control_DF = Control_DF.drop_duplicates(['GUI_1', 'GUI'], inplace=False)

#        Rename columns within the Control_DF to differentiate between new and old GUIs
Control_DF.columns = ['NewGUI', 'ExistingGUI']

########################################################################################################################

# 3.4. Importing confidence metadata (3-step and MESH) / incl. metadata checks
#      This information will be used to build the means for comparing new maps against existing data

##########################
# [THIS SECTION IS WRITTEN IN PYTHON 3.6. AND CAN BE EXECUTED FROM ANY PYTHON CONSOLE / IDE]
##########################

# 3.4.1. Load data from UK_METADATA_&_CONFIDENCE_2012_HOCI_additions spreadsheet
UK_Meta_Confidence = pd.read_excel("Z:\\Marine\\Evidence\\HabitatMapping\\EUNISmapping\\UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls", "Confidence scores")

#        Slice unwanted columns from the UK_Meta_Confidence DataFrame
ThreeStep_GUI_Confidence = UK_Meta_Confidence[['GUI', 'NewTotal', 'Overall score']]


#        Define confidence_check() function to check if the data are missing 3-step confidence scores
def confidence_check(df):
    """
    Function title: confidence_check()
    Define function to check if a 3-step confidence score has been completed for each GUI within the
    attribute table
    """
    data = df['NewTotal']
    # Perform check calculate if a MESH score is present or lacking
    if data >= 0:
        return '3-Step confidence present'
    else:
        return 'Requires 3-Step confidence'


# 3.4.2. Metadata Check 1 - Are there any missing 3-step confidence scores?
#        This score has the greatest weighting in influencing the final outcome

##########################
#    METADATA CHECK 1
##########################

#        Before continuing the process it is important to check if the confidence / MESH data are available to draw
#        accurate comparisons between the intersecting maps. If there are missing entries, these will need to be
#        completed before continuing the analyses.

#        Perform check to test if the data from the UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document
#        have had a 3-step confidence check completed
ThreeStep_GUI_Confidence['Confidence_check'] = ThreeStep_GUI_Confidence.apply(lambda df: confidence_check(df), axis=1)

#        Removing UKSeaMap16 from the data requiring a 3-step confidence check (this is all modelled data)
#        Create variable of all new map intersections where the intersection is not (~) with a UKSM GUI
Non_UKSM_Intersections = Control_DF.loc[~Control_DF['ExistingGUI'].isin(['UKSM'])]

#        Create list for all unique new map GUI values which do not intersect with a UKSM GUI
#        This is used to refine the data pulled in from the UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document
Unique_Not_UKSM = list(Non_UKSM_Intersections['NewGUI'].unique())

#        Create subset of the ThreeStep_GUI_Confidence DF which excludes an new maps which intersect a UKSM GUI
JNCC_Missing_Confidence = ThreeStep_GUI_Confidence.loc[ThreeStep_GUI_Confidence['GUI'].isin(Unique_Not_UKSM)]

#        Adding survey / map names to the GUIs from metadata available within the GUI tracking document
GUI_Tracking = pd.read_excel(r'Z:\Marine\Evidence\HabitatMapping\GUI_tracking.xlsx', 'Sheet1')

#        Slice the GUI_Tracking DF to only include the GUI values and their 'Dataset Title'
GUI_Tracking = GUI_Tracking[['Globally unique ID', 'Dataset Title']]

#        Merge the JNCC_Missing_Confidence data with GUI_Tracking
JNCC_Missing_Confidence = pd.merge(JNCC_Missing_Confidence, GUI_Tracking, left_on='GUI', right_on='Globally unique ID',
                                   how='left')

#        Drop unwanted column data from the JNCC_Missing_Confidence DF
JNCC_Missing_Confidence.drop(['Globally unique ID'], axis=1, inplace=True)

#        Load the JNCC_Missing_Confidence DF to see which maps intersecting new survey maps exist within the
#        UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document and are missing a 3-step confidence score
JNCC_Missing_Confidence_Output = JNCC_Missing_Confidence.loc[
    JNCC_Missing_Confidence['Confidence_check'].isin(['Requires 3-Step confidence'])]

#        Print all data which are missing 3-step confidence values - check these values within the
#        UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document and complete these entries if possible

if JNCC_Missing_Confidence_Output.empty is False:
    # Print this data if there are entries within the DF
    print(JNCC_Missing_Confidence_Output)
    # Export this data to a .csv file if there are entries within the DF
    JNCC_Missing_Confidence_Output.\
        to_csv(
        r'J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\InputData\UKMetaConf2012HOCI_MissingData\JNCC_Missing_Confidence_output.csv',
         sep=',')
else:
    print('No erroneous data present')


# 3.4.3. Metadata Check 2 - Have values been erroneously assigned a 3-step confidence score of 0? Use this indicator to
#        flag any data which require further inspection within the UK Metadata Confidence 2012 HOCI Excel document.

##########################
#    METADATA CHECK 2
##########################

#        Perform secondary check to load all data which have been assigned a 3-step confidence value of 0
#        Although these records have a numerical value, it is potentially erroneous and has been auto-filled within the
#        UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document
Zero_Confidence = JNCC_Missing_Confidence.loc[JNCC_Missing_Confidence['NewTotal'] == 0]

#        Print all data which have 0 3-step confidence values - check these values within the
#        UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document and complete these entries if possible
if Zero_Confidence.empty is False:
        # Print this data if there are entries within the DF
        print(Zero_Confidence)
        print("If data is a 'krieging study' then this should score 0 3-step confidence")
        # Export this data to a .csv file if there are entries within the DF
        Zero_Confidence.to_csv(
            r'J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\InputData\UKMetaConf2012HOCI_MissingData\GUI_Zero_Confidence.csv',
            sep=',')
else:
    print('No erroneous data present')


# 3.4.4. Metadata Check 3 - Are data present within the intersection which do not exist within the
#        UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document

##########################
#    METADATA CHECK 3
##########################

#        Perform tertiary check to load all data which have been intersected but do not appear within the
#        UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document at all. This data will need to be added and MESH /
#        3-step confidence assessments completed.
UK_Meta_Conf_2012HOCI_Missing_GUI = Control_DF.loc[~Control_DF['ExistingGUI'].isin(ThreeStep_GUI_Confidence['GUI'])]

#        Refine to only include the unique values from the existing maps which have been intersected by new survey data
UK_Meta_Conf_2012HOCI_Missing_GUI_Unique = pd.DataFrame(UK_Meta_Conf_2012HOCI_Missing_GUI['ExistingGUI'].unique())

#        Set column name in DF to represent the missing data
UK_Meta_Conf_2012HOCI_Missing_GUI_Unique.columns = ['MissingGUI']

#        Export any data which are intersected but not included within the
#        UK_METADATA_&_CONFIDENCE_2012_HOCI_additions.xls document circulate to mapping team (IF NECESSARY)
if UK_Meta_Conf_2012HOCI_Missing_GUI_Unique.empty is False:
    # Print this data if there are entries within the DF
    print(UK_Meta_Conf_2012HOCI_Missing_GUI_Unique)
    # Export this data to a .csv file if there are entries within the DF
    UK_Meta_Conf_2012HOCI_Missing_GUI_Unique.\
        to_csv(r'J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\InputData\UKMetaConf2012HOCI_MissingData\NotIn_UKMetaConf2012.csv',
               sep=',')
else:
    print('No erroneous data present')


#        If all metadata checks have returned 'No data present' then further analyses are able to be computed
#        accurately. These checks must be completed to ensure the required metadata are present to compare new and
#        existing survey data.

########################################################################################################################

# 3.5. Creating metadata for all new survey maps to be added into the combined map

##########################
# [THIS SECTION IS WRITTEN IN PYTHON 3.6. AND CAN BE EXECUTED FROM ANY PYTHON CONSOLE / IDE]
##########################

# 3.5.1. Import all attribute data from the newly merged maps into a Pandas DataFrame
Merged_Attributes = pd.read_csv(
    r'J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\InputData\New_Merged_Maps_Attributes_30012019.csv',
    low_memory=False)

#        List all unique GUIs present
Merged_Attributes['GUI'].unique()

#        Convert all values within the 'HAB_TYPE' column into strings to facilitate .groupby() aggregation
Merged_Attributes['HAB_TYPE'] = Merged_Attributes['HAB_TYPE'].astype(str)

#        Aggregate all habitat data by individual GUI value using .groupby() and apply to a list
Aggregated_Attributes = Merged_Attributes.groupby(['GUI'])['HAB_TYPE'].apply(list)

#        Convert the Pandas Series Object into a DataFrame to be manipulated later in the script
Aggregated_Attributes = pd.DataFrame(Aggregated_Attributes)

#        Reset the index of the newly created DataFrame to pull all data into correctly formatted columns
Aggregated_Attributes = Aggregated_Attributes.reset_index(inplace=False)

#    Reset the columns within the newly indexed DataFrame
Aggregated_Attributes.columns = ['GUI', 'HAB_TYPE']

#    Run remove_my_nan() function to cleanse the Aggregated_Attributes[''HAB_TYPE'] of all erroneous 'nan' values
Aggregated_Attributes['HAB_TYPE'] = Aggregated_Attributes.apply(lambda df: remove_my_nan(df, 'HAB_TYPE'), axis=1)


# 3.5.2. Classify habitats based on EUNIS Codes present within data
#        Define habitat_classifier() function to categorise HAB_TYPE data into intertidal, subtidal or mixed based on
#        EUNIS values
def habitat_classifier(df):
    """
     Function Title: habitat_classifier()
     Define function to classify data into intertidal, mixed or sub-tidal values based on EUNIS codes present
     """
    # Define values to search by
    intertidal = ['A1', 'A2', 'B3']
    subtidal = ['A3', 'A4', 'A5', 'A6']
    # Pull out all unique habitat codes within target subset
    habitat = df['HAB_TYPE']

    # Run conditional statements
    if any([x in y for x in intertidal for y in habitat]):
        if any([x in y for x in subtidal for y in habitat]):
            return 'Mixed habitat'
        else:
            return 'Intertidal'
    elif any([x in y for x in subtidal for y in habitat]):
        return 'Sub-tidal'
    else:
        return 'Error'


#        Apply habitat classifier to Aggregated_Attributes DataFrame to indicate the habitat type based on the EUNIS
#        codes present within the 'HAB_TYPE' column
Aggregated_Attributes['Habitat_Classification'] = Aggregated_Attributes.apply(lambda df: habitat_classifier(df), axis=1)

#        Create variable with desired fields to be used when merging with MESH confidence DataFrame
Agg_Merge = Aggregated_Attributes[['GUI', 'Habitat_Classification']]

# 3.5.3. Completing confidence checks on new map data

#        Perform left merge between the aggregated map attribute data and the presence / absence MESH confidence data
New_Decision_Attributes = pd.merge(Agg_Merge, ThreeStep_GUI_Confidence, on='GUI', how='left')

#        Run confidence_check() function on merged data and assign result to values which did not match MESH data
New_Decision_Attributes['Confidence_check'] = \
    New_Decision_Attributes.apply(lambda df: confidence_check(df), axis=1)

#        Rename columns within Combined_Decision_Attributes DataFrame to correct values
New_Decision_Attributes.columns = ['GUI', 'Habitat_Classification', '3_Step_Confidence_Score', 'Overall score',
                                   'Confidence_check']

# 3.5.4. Combining data sets - source and new decision DF

#        Assign the merged maps MCZ source data to a new variable 'Merge_MCZ' to be merged into the data used for the
#        decision tree
Merge_MCZ = Merged_Attributes[['GUI', 'MCZ_Source']]

#        Perform left merge between New_Decision_Attributes and MCZ source data field
New_Decision_Attributes = pd.merge(New_Decision_Attributes, Merge_MCZ, on='GUI', how='left')

#    Drop duplicate data from GUI values
New_Decision_Attributes = New_Decision_Attributes.drop_duplicates(subset=['GUI'], inplace=False)

########################################################################################################################

# 3.6. Creating metadata for the intersected existing maps

##########################
# [THIS SECTION IS WRITTEN IN PYTHON 3.6. AND CAN BE EXECUTED FROM ANY PYTHON CONSOLE / IDE]
##########################

# 3.6.1. Pull out all combined map GUIs which have an intersecting reference map
Combined_GUI = pd.DataFrame(Intersected_Maps['CombinedMap_GUI'])

#        Subset intersection attributes by GUIs which are have a combined map GUI that intersects with a reference map
#        GUI
Combined_Attributes = Intersection_Attributes.loc[
    Intersection_Attributes['GUI'].isin(Combined_GUI['CombinedMap_GUI'])]

#        Create variable all combined map habitat types aggregated by targeted GUI values
Combined_Aggregated_Attributes = Combined_Attributes.groupby(['GUI'])['HAB_TYPE'].apply(list)

#        Convert the Pandas Series Object into a DataFrame to be manipulated later in the script
Combined_Aggregated_Attributes = pd.DataFrame(Combined_Aggregated_Attributes)

#        Reset index of newly created DataFrame to pull data into correctly formatted columns
Combined_Aggregated_Attributes = Combined_Aggregated_Attributes.reset_index(inplace=False)

#        Reset columns within the newly indexed DataFrame
Combined_Aggregated_Attributes.columns = ['GUI', 'HAB_TYPE']

#        Utilise remove_my_nan() function to cleanse the DataFrame / habitat data of all erroneous 'nan' values
Combined_Aggregated_Attributes['HAB_TYPE'] = Combined_Aggregated_Attributes.apply(
    lambda df: remove_my_nan(df, 'HAB_TYPE'), axis=1)

# 3.6.2. Classifying habitat data based on EUNIS Codes present

# Apply habitat classifier to Aggregated_Attributes DataFrame to indicate the habitat type based on the EUNIS present
# within the 'HAB_TYPE' column
Combined_Aggregated_Attributes['Habitat_Classification'] = \
    Combined_Aggregated_Attributes.apply(lambda df: habitat_classifier(df), axis=1)

# Create variable with desired fields to be used when merging with MESH confidence DataFrame
Comb_Agg_Merge = Combined_Aggregated_Attributes[['GUI', 'Habitat_Classification']]

# Perform left merge between the aggregated map attribute data and the presence / absence MESH confidence data
Combined_Decision_Attributes = pd.merge(Comb_Agg_Merge, ThreeStep_GUI_Confidence, on='GUI', how='left')

# 3.6.3. Completing confidence checks on the intersected maps

# Run confidence_check() function on merged data and assign result to values which did not match MESH data
Combined_Decision_Attributes['Confidence_check'] = \
    Combined_Decision_Attributes.apply(lambda df: confidence_check(df), axis=1)

# Rename columns within Combined_Decision_Attributes DataFrame
Combined_Decision_Attributes.columns = ['GUI', 'Habitat_Classification', '3_Step_Confidence_Score', 'Overall score',
                                        'Confidence_check']

# Load in combined merge maps MCZ source data
Combined_MCZ = Combined_Attributes[['GUI', 'MCZ_Original_survey']]  # Not sure if this is correct??

# 3.6.4. Combining data sets - source and main decision DF

# Perform left merge between Combined_Decision_Attributes and MCZ source data field
Combined_Decision_Attributes = pd.merge(Combined_Decision_Attributes, Combined_MCZ, on='GUI', how='left')

# Drop duplicate data from GUI values
Combined_Decision_Attributes = Combined_Decision_Attributes.drop_duplicates(subset=['GUI'], inplace=False)

########################################################################################################################

# 3.7. Run the 5 stage decision tree analysis on the existing and new maps - comparing new and existing data

##########################
# [THIS SECTION IS WRITTEN IN PYTHON 3.6. AND CAN BE EXECUTED FROM ANY PYTHON CONSOLE / IDE]
##########################

# 3.7.1. Creating the comparison data set
Comparison_DF = Control_DF

#        Name comparison data columns appropriately
Comparison_DF.columns = ['NewGUI', 'ExistingGUI']

#        Merge new attribute data with Comparison_DF
Comparison_DF = pd.merge(Comparison_DF, New_Decision_Attributes, left_on='NewGUI', right_on='GUI')

#        Rename columns to prevent data to indicate which attributes are from the new data
Comparison_DF.columns = ['NewGUI', 'ExistingGUI', 'GUI', 'New_Habitat_Classification', 'New_3_Step_Confidence_Score',
                         'New_MESH_Score', 'New_Confidence_check', 'New_MCZ_Source']

#        Merge existing attribute data with Comparison_DF
Comparison_DF = pd.merge(Comparison_DF, Combined_Decision_Attributes, left_on='ExistingGUI', right_on='GUI')

#        Rename columns to assign attributes to new / old data
Comparison_DF.columns = [
    'NewGUI', 'ExistingGUI', 'GUI_x', 'New_Habitat_Classification', 'New_3_Step_Confidence_Score', 'New_MESH_Score',
    'New_Confidence_check', 'New_MCZ_Source', 'GUI_y', 'Existing_Habitat_Classification',
    'Existing_3_Step_Confidence_Score', 'Existing_MESH_Score', 'Existing_Confidence_check',
    'Existing_MCZ_Original_survey']

#        Drop unwanted columns from Comparison_DF and reorder remaining columns into correct format
Comparison_DF.drop(['GUI_x', 'GUI_y', 'New_Confidence_check', 'Existing_Confidence_check'], axis=1, inplace=True)

#        Rearrange columns in correctly formatted order
Comparison_DF = Comparison_DF[[
    'NewGUI', 'ExistingGUI', 'New_Habitat_Classification', 'Existing_Habitat_Classification',
    'New_3_Step_Confidence_Score', 'Existing_3_Step_Confidence_Score', 'New_MESH_Score', 'Existing_MESH_Score',
    'New_MCZ_Source', 'Existing_MCZ_Original_survey']]

#        Replace 'NaN' values with 0 to allow for decision tree analysis to complete accurately
Comparison_DF['New_3_Step_Confidence_Score'].fillna(0, inplace=True)
Comparison_DF['Existing_3_Step_Confidence_Score'].fillna(0, inplace=True)
Comparison_DF['New_MESH_Score'].fillna(0, inplace=True)
Comparison_DF['Existing_MESH_Score'].fillna(0, inplace=True)


# 3.7.2. Defining the decision tree

# Define decision_tree() function
# Function Title: decision_tree()
def decision_tree(df):
    """Create evaluation mechanism to complete step-wise JNCC decision tree analysis"""
    # Return the new GUI if the new map is intertidal only
    if df['New_Habitat_Classification'] == 'Intertidal':
        return df['NewGUI']

    # Run analysis if the new map comprises mixed habitats
    elif df['New_Habitat_Classification'] == 'Mixed habitat':

        # Return the existing GUI if the existing map is intertidal and the new map is mixed or sub-tidal
        if df['Existing_Habitat_Classification'] == 'Intertidal':
            return df['ExistingGUI']

        # Run further analyses if the new map comprises mixed habitats and the existing map is sub-tidal
        # (neither are prioritised)
        elif df['Existing_Habitat_Classification'] == 'Sub-tidal':

            # Return the new GUI if the new map has a greater 3 step confidence score than the existing map
            if df['New_3_Step_Confidence_Score'] > df['Existing_3_Step_Confidence_Score']:
                return df['NewGUI']

            # Return the existing GUI if the existing map has a greater 3 step confidence score than the new map
            elif df['New_3_Step_Confidence_Score'] < df['Existing_3_Step_Confidence_Score']:
                return df['ExistingGUI']

            # Run further analyses if both maps have equal 3 step confidence scores (neither is prioritised)
            elif df['New_3_Step_Confidence_Score'] == df['Existing_3_Step_Confidence_Score']:
                # Compare data sources from two data sets - NOT CURRENTLY POSSIBLE / MISSING DATA?

                # Return the new GUI if the new map has a greater MESH confidence score than the existing map
                if df['New_MESH_Score'] > df['Existing_MESH_Score']:
                    return df['NewGUI']

                # Return the existing GUI if the existing map has a greater MESH confidence score than the new map
                elif df['New_MESH_Score'] < df['Existing_MESH_Score']:
                    return df['ExistingGUI']

                # If neither MESH confidence score takes priority, then flag the map as requiring expert judgement
                elif df['New_MESH_Score'] == df['Existing_MESH_Score']:
                    return 'Requires expert judgement'

        # Run further analyses if the new map comprises mixed habitats and the existing map is also mixed
        # (neither are prioritised)
        elif df['Existing_Habitat_Classification'] == 'Mixed habitat':

            # Return the new GUI if the new map has a greater 3 step confidence score than the existing map
            if df['New_3_Step_Confidence_Score'] > df['Existing_3_Step_Confidence_Score']:
                return df['NewGUI']

            # Return the existing GUI if the existing map has a greater 3 step confidence score than the new map
            elif df['New_3_Step_Confidence_Score'] < df['Existing_3_Step_Confidence_Score']:
                return df['ExistingGUI']

            # Run further analyses if both maps have equal 3 step confidence scores (neither is prioritised)
            elif df['New_3_Step_Confidence_Score'] == df['Existing_3_Step_Confidence_Score']:
                # Compare data sources from two data sets - NOT CURRENTLY POSSIBLE / MISSING DATA?

                # Return the new GUI if the new map has a greater MESH confidence score than the existing map
                if df['New_MESH_Score'] > df['Existing_MESH_Score']:
                    return df['NewGUI']

                # Return the existing GUI if the existing map has a greater MESH confidence score than the new map
                elif df['New_MESH_Score'] < df['Existing_MESH_Score']:
                    return df['ExistingGUI']

                # If neither MESH confidence score takes priority, then flag the map as requiring expert judgement
                elif df['New_MESH_Score'] == df['Existing_MESH_Score']:
                    return 'Requires expert judgement'

    # Run analysis if the new map comprises sub-tidal habitats
    elif df['New_Habitat_Classification'] == 'Sub-tidal':

        # Return the existing GUI if the existing map is intertidal and the new map is mixed or sub-tidal
        if df['Existing_Habitat_Classification'] == 'Intertidal':
            return df['ExistingGUI']

        # Run further analyses if the new map comprises mixed habitats and the existing map is sub-tidal
        # (neither are prioritised)
        elif df['Existing_Habitat_Classification'] == 'Sub-tidal':

            # Return the new GUI if the new map has a greater 3 step confidence score than the existing map
            if df['New_3_Step_Confidence_Score'] > df['Existing_3_Step_Confidence_Score']:
                return df['NewGUI']

            # Return the existing GUI if the existing map has a greater 3 step confidence score than the new map
            elif df['New_3_Step_Confidence_Score'] < df['Existing_3_Step_Confidence_Score']:
                return df['ExistingGUI']

            # Run further analyses if both maps have equal 3 step confidence scores (neither is prioritised)
            elif df['New_3_Step_Confidence_Score'] == df['Existing_3_Step_Confidence_Score']:
                # Compare data sources from two data sets - NOT CURRENTLY POSSIBLE / MISSING DATA?

                # Return the new GUI if the new map has a greater MESH confidence score than the existing map
                if df['New_MESH_Score'] > df['Existing_MESH_Score']:
                    return df['NewGUI']

                # Return the existing GUI if the existing map has a greater MESH confidence score than the new map
                elif df['New_MESH_Score'] < df['Existing_MESH_Score']:
                    return df['ExistingGUI']

                # If neither MESH confidence score takes priority, then flag the map as requiring expert judgement
                elif df['New_MESH_Score'] == df['Existing_MESH_Score']:
                    return 'Requires expert judgement'

        # Run further analyses if the new map comprises sub-tidal habitats and the existing map is also mixed
        # (neither are prioritised)
        elif df['Existing_Habitat_Classification'] == 'Mixed habitat':

            # Return the new GUI if the new map has a greater 3 step confidence score than the existing map
            if df['New_3_Step_Confidence_Score'] > df['Existing_3_Step_Confidence_Score']:
                return df['NewGUI']

            # Return the existing GUI if the existing map has a greater 3 step confidence score than the new map
            elif df['New_3_Step_Confidence_Score'] < df['Existing_3_Step_Confidence_Score']:
                return df['ExistingGUI']

            # Run further analyses if both maps have equal 3 step confidence scores (neither is prioritised)
            elif df['New_3_Step_Confidence_Score'] == df['Existing_3_Step_Confidence_Score']:
                # Compare data sources from two data sets - NOT CURRENTLY POSSIBLE / MISSING DATA?

                # Return the new GUI if the new map has a greater MESH confidence score than the existing map
                if df['New_MESH_Score'] > df['Existing_MESH_Score']:
                    return df['NewGUI']

                # Return the existing GUI if the existing map has a greater MESH confidence score than the new map
                elif df['New_MESH_Score'] < df['Existing_MESH_Score']:
                    return df['ExistingGUI']

                # If neither MESH confidence score takes priority, then flag the map as requiring expert judgement
                elif df['New_MESH_Score'] == df['Existing_MESH_Score']:
                    return 'Requires expert judgement'


# 3.7.3. Executing the decision tree

# Run decision tree analysis on the combined Comparison_DF
Comparison_DF['Comparison_Result'] = Comparison_DF.apply(lambda df: decision_tree(df), axis=1)

# 3.7.4. Analysing decision results

# Output the comparison table as a csv
Comparison_DF.to_csv(r'J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\NewCombinedMap_ComparisonOutput\NewCombinedMap_ComparisonOutput.csv', sep=',')

#    Perform QC check to identify if any data have been flagged as requiring expert judgement
#    Pull out erroneous data which requires expert judgement into separate DF
Requires_Judgement = Comparison_DF.loc[Comparison_DF['Comparison_Result'].isin(['Requires expert judgement'])]

########################################################################################################################

# 3.8. Joining decision results to geospatial data

##########################
# [THIS SECTION IS WRITTEN IN PYTHON 3.6. AND CAN BE EXECUTED FROM ANY PYTHON CONSOLE / IDE]
##########################

#      Loading the comparison results into a format to be attached to the new survey data / combined map intersection
#      This information must be added as a table and then exported to the working geodatabase as a .dbf format file.

#      Subset Comparison_DF to only include GUI values and comparison result - this will be joined as a .dbf file to
#      both sets of map data stored within the intersected layer
Join_Results = Comparison_DF[['NewGUI', 'ExistingGUI', 'Comparison_Result']]

#      Export Join_Results DF as a .csv file to be joined onto the intersected layer within ArcGIS as a .dbf
Join_Results.to_csv(r'J:\GISprojects\Marine\HabitatMapping\Combined_Map_Updates_LM\NewCombinedMap_ComparisonOutput\Join_Results.csv', sep=',')


##########################
# [THIS SECTION IS WRITTEN IN ARCPY AND CAN ONLY BE EXECUTED FROM ESRI ArcGIS PYTHON CONSOLE]
##########################

#      Join the Join_Results table by attributes to the intersected new survey maps / combined map layer
#      This must be completed for both old and new GUI values to either respective data entry within the intersect layer

#      Complete a select by attribute on the intersected survey / combined map layer
#      'new_maps_dissoved_combinedmap_intersect' to identify data where the new GUI value is not equal to the
#      'Comparison_Result' field acquired by joining the 'Join_Results' .dbf file - unable to get to work?
arcpy.SelectLayerByAttribute_management("new_maps_dissoved_combinedmap_intersect_30012019", "NEW_SELECTION", "new_maps_dissoved_combinedmap_intersect_30012019.GUI_1 <> 'Combined_Result'))")

#      Export the output of the above select query as 'Survey_comb_intersection_newGUI_lose' and utilise this layer to
#      erase unwanted areas from the 'new_maps_dissolved' new survey data - save this layer as 'New_maps_win_processed'
arcpy.Erase_analysis("new_maps_dissolved_24012019", "Survey_comb_intersection_newGUI_lose", r"Insert output gdb filepath here \New_maps_win_processed31012019", "#")

########################################################################################################################

# 3.9. Readying the intersected new survey / combined map data for overwriting

##########################
# [THIS SECTION IS WRITTEN IN ARCPY AND CAN ONLY BE EXECUTED FROM ESRI ArcGIS PYTHON CONSOLE]
##########################

#      Re-select by attributes all the combined map areas (updated with UKSM18) which exclude NE Evidence Base data.
#      The previous iteration of this also removed UKSM data, whereas, we now wish to retain that information.
arcpy.SelectLayerByAttribute_management("combinedmap_UKSM18_updated", "NEW_SELECTION", "Source IN ('NE_Ev_2', 'NE_Evid'))")
arcpy.SelectLayerByAttribute_management("combinedmap_UKSM18_updated", "SWITCH_SELECTION", "Source IN ('NE_Ev_2', 'NE_Evid')")

#    OR IF YOUR'RE SURE THERE'S NO NULLS IN SOURCE FIELD
arcpy.SelectLayerByAttribute_management("combinedmap_UKSM18_updated", "NEW_SELECTION", "Source NOT IN ('NE_Ev_2', 'NE_Evid')")

#    Export the data selected using the above query from the combinedmap_UKSM18_updated layer as
#    combinedmap_UKSM18_updated_no_NEevidencebase - this layer will form the basis of data which will be erased by the
#    new winning survey maps.

#    Perform an erase to remove the areas of the 'combinedmap_UKSM18_updated_no_NEevidencebase' which coincide with the
#    winning new survey data 'New_maps_win_processed' - this will prevent overlaps when adding the new survey data back
#    into the combined map
arcpy.Erase_analysis("MasterData/combinedmap_UKSM18_updated_no_NEevidencebase_01022019","NewSurveyUpdates/New_maps_win_processed31012019","J:/GISprojects/Marine/HabitatMapping/Combined_Map_Updates_LM/InputData/working_geodatabase.gdb/combinedmap_updated_surveydata_placeholder_01022019","#")

#    Merge the winning new survey data 'New_maps_win_processed' back into the
#    'combinedmap_updated_surveydata_placeholder' layer to prepare for the reinsertion of the NE Evidence Base data


########################################################################################################################

#                          4. REINSERTING THE NE EVIDENCE BASE INTO THE COMBINED MAP                                   #

########################################################################################################################

# 4.1. Reinserting the NE Evidence Base into the combined map

