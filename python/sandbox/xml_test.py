import xml.etree.ElementTree as ET

string='<data description="desc" function="e=mc^2" value="2"><property /></data>'
    
root=ET.fromstring(string)