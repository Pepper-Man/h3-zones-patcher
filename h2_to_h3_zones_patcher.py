import os
import re
import configparser
import subprocess
import xml.etree.ElementTree as ET

# File Paths
config = configparser.ConfigParser()
config.read('options.ini')
h3ek_directory = config['config']['root_h3ek_directory']
h2ek_directory = config['config']['root_h2ek_directory']
extr_scen = config['config']['extracted_h2_scenario']

# Extract zone data
scenfile = ET.parse(extr_scen.strip('"'))
root = scenfile.getroot()

zones_start_blocks = root.findall(".//block[@name='zones']")

# Get all zone names
for zones_block in zones_start_blocks:
    zones_end = False
    zones_list = []
    i = 0
    while(zones_end == False):
        search_string = "./element[@index='" + str(i) + "']"
        element = zones_block.find(search_string)
        
        if element is not None:
            #zones_list.append(i)
            zones_list.append(element.find("./field[@name='name']").text.strip())
            i += 1
        else:
            zones_end = True
 
open("zones_output.txt", 'w').close()
out = open("zones_output.txt", "a")
           
# Get areas and firing positions for each zone
i = 0
for zone_name in zones_list:
    # Areas
    out.write("Zone: " + zone_name + "\nAreas:\n")
    areas_block_list = root.find(".//block[@name='zones']").find("./element[@index='" + str(i) + "']").findall(".//block[@name='areas']")
    for area_block in areas_block_list:
        areas_end = False
        j = 0
        while (areas_end == False):
            search_string = "./element[@index='" + str(j) + "']"
            element = area_block.find(search_string)
            
            if element is not None:
                out.write(element.find("./field[@name='name']").text.strip() + "\n")
                out.write(element.find("./field[@name='area flags']").text.strip() + "\n")
                out.write(element.find("./field[@name='runtime starting index']").text.strip() + "\n")
                out.write(element.find("./field[@name='runtime count']").text.strip() + "\n")
                out.write(element.find("./field[@name='manual reference frame']").text.strip() + "\n")
                j += 1
            else:
                areas_end = True
    
    
    # Firing positions
    out.write("Firing Positions:")
    fpos_block_list = root.find(".//block[@name='zones']").find("./element[@index='" + str(i) + "']").findall(".//block[@name='firing positions']")
    for fpos_block in fpos_block_list:
        fpos_end = False
        j = 0
        while (fpos_end == False):
            search_string = "./element[@index='" + str(j) + "']"
            element = fpos_block.find(search_string)
            
            if element is not None:
                out.write("index = " + str(j) + "\n")
                out.write(element.find("./field[@name='position (local)']").text.strip() + "\n")
                out.write(element.find("./field[@name='reference frame']").text.strip() + "\n")
                out.write(element.find("./field[@name='flags']").text.strip() + "\n")
                out.write(element.find("./block_index[@name='short block index']").attrib['index'].strip() + "\n")
                out.write(element.find("./field[@name='cluster index']").text.strip() + "\n")
                out.write(element.find("./field[@name='normal']").text.strip() + "\n")
                j += 1
            else:
                fpos_end = True

    i += 1
out.close()

# DATA EXTRACTION DONE
#####################################################
# USER MANUAL ADDING TIME

with open('zones_output.txt', 'r') as data:
    text = data.readlines()

zones_count = 0
areas_count = 0
fpos_count = 0

for line in text:
    if ("Zone:" in line):
        if (zones_count != 0):
           print ("Zone " + str(zones_count) + " needs " + str(areas_count) + " areas and " + str(fpos_count) + " firing positions!") 
        areas_count = 0
        fpos_count = 0
        zones_count += 1
    if ("areas" in line):
        areas_count += 1
    if ("index = " in line):
        fpos_count += 1

data.close()

while (True):  
    choice = input("\nPlease add the correct number of areas and firing positions\nto each zone as per the information above.\nType \"continue\" once done to begin the patching process:\n")
    if (choice.lower() == "continue"):
        break
    
# DATA CONVERSION DONE
#####################################################
# PATCHING START

def run_tool(field, data):
    toolpath = h3ek_directory.strip('"') + '\\tool.exe'
    command = [toolpath, "patch-tag-field", "pepperh2\levels\oldmombasa\oldmombasa.scenario", field, data]
    os.chdir(h3ek_directory.replace('\\', '/').strip('"'))
    process = subprocess.Popen(' '.join(f'"{arg}"' for arg in command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    print(output.decode('utf-8'))
    print(error.decode('utf-8'))

with open('zones_output.txt', 'r') as data:
    text = data.readlines()

open("batched_commands.txt", 'w').close() # Clear previous commands
bch_out = open('batched_commands.txt', 'a')

zone = -1
areas = False
fpos = False
area_index = -1
area_data_count = 0
previous_was_actualflag = False

for line in text:
    if ("Zone:" in line):
        zone += 1
        print("next zone")
        # line is zone header
        continue
    elif ("Areas:" in line):
        # line is areas header
        areas = True
        fpos = False
        area_index = 0
        area_data_count = 0
        continue
    elif ("Firing Positions:" in line):
        # line is fpos header
        fpos = True
        areas = False
        continue
    elif (areas):
        # line is area data
        if (previous_was_actualflag):
            previous_was_actualflag = False
            continue
        if (area_data_count == 0):
            # line is area name
            field_path = "scenario_struct_definition[0].zones[" + str(zone) + "].areas[" + str(area_index) + "].name"
            print("patching " + line.strip())
            run_tool(field_path, line.strip())
            area_data_count += 1
        elif (area_data_count == 1):
            # line is area flags
            field_path = "scenario_struct_definition[0].zones[" + str(zone) + "].areas[" + str(area_index) + "].area flags"
            print("area flags")
            run_tool(field_path, line.strip())
            area_data_count += 1
            if (line.strip() != "0"):
                previous_was_actualflag = True
        elif (area_data_count == 2):
            # line is runtime starting index
            area_data_count += 1
            continue
        elif (area_data_count == 3):
            # line is runtime count
            area_data_count += 1
            continue
        elif (area_data_count == 4):
            # line is manual reference frame
            field_path = "scenario_struct_definition[0].zones[" + str(zone) + "].areas[" + str(area_index) + "].manual reference frame"
            print("manual ref frame = " + line.strip())
            run_tool(field_path, ",-1")
            area_data_count = 0
            area_index += 1
        
### FIRING POSITION FUNCTIONALITY


bch_out.close()
for fire_pos in all_positions:
    fire_pos = fire_pos.split('\n')
    count = 0
    index = ""
    position = ""
    ref_frame = ""
    flags = ""
    area = ","
    cluster = ""
    normal = ""
    for parameter in fire_pos:
        if (count == 0):
            index = parameter
            count += 1
            continue
        if (count == 1):
            position = parameter
            count += 1
            continue
        if (count == 2):
            ref_frame = parameter
            count += 1
            continue
        if (count == 3):
            flags = parameter
            count += 1
            continue
        if (count == 4):
            area += parameter
            count += 1
            continue
        if (count == 5):
            cluster = parameter
            count += 1
            continue
        if (count == 6):
            normal = parameter
            count += 1
            continue
        if (count > 6):
            count = 0
    
    position_field = "scenario_struct_definition[0].zones[" + str(zone_index) + "].firing positions[" + index + "].position (local)"
    frame_field = "scenario_struct_definition[0].zones[" + str(zone_index) + "].firing positions[" + index + "].reference frame"
    flag_field = "scenario_struct_definition[0].zones[" + str(zone_index) + "].firing positions[" + index + "].flags"
    area_field = "scenario_struct_definition[0].zones[" + str(zone_index) + "].firing positions[" + index + "].area"
    cluster_field = "scenario_struct_definition[0].zones[" + str(zone_index) + "].firing positions[" + index + "].cluster index"
    normal_field = "scenario_struct_definition[0].zones[" + str(zone_index) + "].firing positions[" + index + "].normal"
    
    run_tool(position_field, position)
    run_tool(frame_field, ref_frame)
    run_tool(flag_field, flags)
    run_tool(area_field, area)
    run_tool(cluster_field, cluster)
    run_tool(normal_field, normal)
    
    print("firing position " + index + " done")