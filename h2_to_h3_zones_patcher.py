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
for zone_name in zones_list:
    # Areas
    out.write("Zone: " + zone_name + "\nAreas:\n")
    i = 0
    areas_block_list = root.find(".//block[@name='zones']").find("./element[@index='" + str(i) + "']").findall(".//block[@name='areas']")
    for area_block in areas_block_list:
        areas_end = False
        areas_list = []
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
    i += 1
    
    # Firing positions
    out.write("\nFiring Positions: \n")
    fpos_block_list = root.find(".//block[@name='zones']").find("./element[@index='" + str(i) + "']").findall(".//block[@name='firing positions']")
out.close()

# Zone file handling
open("zone_data.xml", 'w').close()
f = open("zone_data.xml", "r")
lines = f.readlines()

# Begin data processing
current_line_count = 0

for line in lines:
    if (current_line_count == -1):
        current_line_count = 0
        continue
    
    # index
    if (current_line_count == 0):
        if ("element" in line):
            index = line.split('"')[1::2]
            out.write(index[0] + "\n")
            current_line_count += 1
            continue
        else:
            # reached end of firing positions
            print("end of positions")
            break
    
    # world position 
    if (current_line_count == 1):
        start = line.index('>') + 1
        arrow_locs = [s.start() for s in re.finditer('<', line)]
        out.write(line[start:arrow_locs[1]] + "\n")
        current_line_count += 1
        continue

    # reference frame
    if (current_line_count == 2):
        start = line.index('>') + 1
        arrow_locs = [s.start() for s in re.finditer('<', line)]
        out.write(line[start:arrow_locs[1]] + "\n")
        current_line_count += 1
        continue
        
    # flags header
    if (current_line_count == 3):
        current_line_count += 1
        continue
    
    # flag number
    if (current_line_count == 4):
        out.write(line.strip() + "\n")
        current_line_count += 1
        continue
    
    # further data
    if (current_line_count > 4):  
        if ("short block index" not in line and "cluster index" not in line and "normal" not in line):
            # line is therefore extra flag data, ignore
            current_line_count += 1
            continue
        else:
            if ("short block index" in line):
                # block index
                equals_signs = [s.start() for s in re.finditer('=', line)]
                end = line.index('>') + 1
                out.write(line[equals_signs[2] + 2:end - 2]  + "\n")
                current_line_count += 1
                continue
            elif ("cluster index" in line):
                # cluster index
                start = line.index('>') + 1
                arrow_locs = [s.start() for s in re.finditer('<', line)]
                out.write(line[start:arrow_locs[1]] + "\n")
                current_line_count += 1
                continue
            else:
                # normals directions
                start = line.index('>') + 1
                arrow_locs = [s.start() for s in re.finditer('<', line)]
                out.write(line[start:arrow_locs[1]] + "\n" + "\n")
                current_line_count = -1
                continue
            
# DATA CONVERSION DONE
#####################################################
# PATCHING START

"""
# Edit this variable to change zone (0-based)
zone_index = 2

with open('zones_output.txt', 'r') as data:
    text = data.read()
    
all_positions = text.split('\n\n')

def run_tool(field, data):
    command = ["tool.exe", "patch-tag-field", "pepperh2\levels\oldmombasa\oldmombasa.scenario", field, data]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    print(output.decode('utf-8'))
    print(error.decode('utf-8'))

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
"""