# h3-zones-patcher
Python script for patching H2 zones/areas/firing positions into a H3 scenario

# Usage
* Extract H2 scenario to XML with `tool export-tag-to-xml`
* Fill in the `options.ini` with your filepaths
* Run .py script
* Add relevant blank zones, areas and firing positions to your scenario via Sapien/Guerilla, based on the output of the python script
* Allow the script to continue once ready
* Wait, hope and pray for success - due to the slow nature of `tool` when patching tags, this may take several hours to patch in every firing position for every area of every zone in an entire H2 scenario. Still better than doing thousands manually!