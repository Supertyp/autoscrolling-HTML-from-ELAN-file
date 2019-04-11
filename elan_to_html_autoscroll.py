# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 13:57:52 2018

take appart a ELAN file and turns it into a basic HTML file:
- autoscroll of text following the audio
- clickable text element, audio jupms to that spot
 
customising:

file: 
    point to the ELAN (.eaf) file you want to import
    
fout: 
    the name of the output.html file  
    
output_order: 
    list two tiers you want to display in the website
    
    first element in output_order should be tier-name with original text
    second element should be translation
    
audio_name: mp3 file that accompanies the ELAN file include extension 
    audio_name = 'example.mp3'
 

author: Wolfgang Barth
wolfgang.barth@anu.edu.au
ERC Centre of Excellence for the Dynamics of Language
Australian National University 
"""

from bs4 import BeautifulSoup
import collections


file = open('C:/path/to/sourceFile.eaf', 'r', encoding="utf8")
fout = open('C:/path/to/outputFile.html', 'w', encoding="utf8")
output_order = ['tierOfSource', 'TierWithTranslation', 0] # the number can be changed to add seconds to the timing
audio_name = 'test.mp3'

# header text icludes the css      
headText = '''<!DOCTYPE html>

<html>
<head>
<meta charset="UTF-8">
<style>

.audio-style {
   width: 50%%;
   margin-left: auto;
   margin-right: auto;
   display: table;
   border: 1px solid grey;

}
.divTable {
	#display: table;
	overflow: auto;
	width: 50%%;
   border: 1px solid grey;
	margin-left: auto;
   margin-right: auto;
	height: 300px;
}

table.first {
    border: 1px solid lightgrey;
    display: column;
    padding: 5px;
	 width: 100%%;
    cursor: pointer;
}

th {
    text-align:left;
    font-size: 20px;
    font-family: "Arial";
    color: green;
}

td.gloss {
    text-align:left;
    font-size: 15px;
    font-family: "Arial";
    color: grey;
}

td.text {
    text-align:left;
    font-size: 15px;
    font-family: "Arial";
    color: black;
}
.picture {
    display: block;
    margin-left: auto;
    margin-right: auto;
    width: 50%%;
    height: auto;
    border: 1px solid grey;
}
</style>
 
<title>CoEDL - Corpus kwic</title>

</head>

<body>
<h1 id="demo" align="center">David Galbbuma</h1>

<img src="test_image.png" class="picture" alt="no image available">

<audio id="myAudio" controls class='audio-style' source src="%s" type="audio/mp3">
  Your browser does not support the audio element.
</audio>
<div class="divTable">
  '''

# the end icludes thejavaSript for the scroll window
end = """
</div>
<script>

// Get the audio element
var vid = document.getElementById("myAudio");

function setCurTime(time) { 
    // change time of audio to where the clicked on text is spoken
    vid.currentTime=time;
    vid.autoplay = true;
}

// Assign an ontimeupdate event to the audio element, 
// and execute a function if the current playback position has changed
vid.ontimeupdate = function() {myFunction()};

function myFunction() {
    // change the background color of the table elements
    // depending on the current position of the audio
    
    var secondsFull = vid.currentTime;
    var seconds = parseInt(secondsFull, 10);
    var secondsOff = seconds;
    
    // record current position to anchor div in window
    var x = window.scrollX, y = window.scrollY;
    
    // highlight current table/text element
    var elmnt = document.getElementById(seconds);
    elmnt.style.backgroundColor = "#f9e79f"
    
    // scroll to previous table/text element so current element is kind of
    // in the middle of scroll div
    var elmntOff = document.getElementById(secondsOff);
    elmntOff.scrollIntoView({behavior: 'smooth'});
    
    // set current position
    window.scrollTo(x, y);   
}
 
</script>
 </body>
</html>"""

# pices are added for each tier
pieces = """  <table id="%s" class="first" onclick="setCurTime(%s)">
		<tr><th class="head">%s</th></tr>
		<tr><td class="text">%s</td></tr>   
	</table>
    """

def make_elan_time_dict(soup):
    
    """ read all time_slot tags from eaf file into a dict 
    """
    
    timeDict = {}
    
    timeSlots = soup.find_all('time_slot')
    for slot in timeSlots:
        timeDict[str(slot.attrs['time_slot_id'])] = str(slot.attrs['time_value'])
    
    return timeDict


def make_file_annotation_dict(soup, timeDict):
    
    """ find all annotations in the soup
        and build dict for each anntotation with all information
    """
    
    fileAnnotationDict = {}
    refDict = {}
    
    tiers = soup.find_all('tier')
    
    for tier in tiers:
        tier_id = tier['tier_id']
        
        annotationDict = {}
        annotations = tier.find_all('annotation')
        
        for x in annotations:
            
            content = x.findChildren()[1].contents
            print (content)
            annotationDict = {'content': ''.join(content)}
            
            annotationString = str(x.findChildren()[0])
            annotationMeta = annotationString.split('>')[0]
            
            for x in annotationMeta.split(' ')[1:]:
                attribute = x.split('="')[0]
                value = x.split('="')[1][:-1]
                annotationDict[attribute] = value
                
                annotationDict[attribute] = value
            
            # some annotations are primary
            # some are reference annotations which refer back to primary annotations
            for k, v in annotationDict.items():
                print (str(k) + ' - ' + str(v))
                if k == 'time_slot_ref1':
                    refDict[annotationDict['annotation_id']] = timeDict[v]
                    
                elif k == 'annotation_ref':
                    refDict[annotationDict['annotation_id']] = refDict[annotationDict['annotation_ref']]
    
            annotationDict['time'] = int(refDict[annotationDict['annotation_id']])
            annotationDict['tier'] = tier_id
            
            fileAnnotationDict[annotationDict['annotation_id']] = annotationDict
 
    return fileAnnotationDict


def make_html_file(fileAnnotationDict, fout, audio_name):
    
    # write head to file
    fout.write(headText % audio_name)
    
    
    # annotations are not always in chronological order in the ELAN file
    # the write Dict catches all relevant annotations and in a second step the 
    # write dict is ordered chronologically
    
    writeDict = {}
    for k, v in fileAnnotationDict.items():
        
        # only the two main tiers are collected (original language and translation)
        if v['tier'] in output_order:
            
            #print (str(k) + ' - ' + str(v))
            
            # create dict for each annotations by time 
            if v['time'] not in writeDict:
                writeDict[v['time']] = {}
                writeDict[v['time']][v['tier']] = v['content']
            else:
                writeDict[v['time']][v['tier']] = v['content']
    
    # order the dictionary by the k (time)
    od = collections.OrderedDict(sorted(writeDict.items()))
    
    #print (str(od))
    
    
    
    # for each in the ordered list create a table item to display
    for k, v in od.items():
        
        offset = output_order[2] # to cut seconds off the audio for alignment
         
        # print (str(k) , v[output_order[0]], v[output_order[1]])
        #print (str(v))
        
        time_info = str((k/1000)  + offset ).split('.')[0] # time stamp in milliseconds transformed to seconds
        
        if output_order[0] not in v:
            first = ' '
        else:
            first = v[output_order[0]]
        
        if output_order[1] not in v:
            second = ' '
        else:
            second = v[output_order[1]]
        
        # write the table item to output file
        fout.write(pieces % (time_info, time_info, first, second))

    # write end to file
    fout.write(end)


def elan_to_html(file):
    
    """ create a timeDict for all time steps 
        create dictionary with all annotations
        create output file
    
    """
    soup = BeautifulSoup(file, 'lxml')
    
    timeDict  = make_elan_time_dict(soup) # dictionary with time_slot and time value information
    
    fileAnnotationDict = make_file_annotation_dict(soup, timeDict)
    
    make_html_file(fileAnnotationDict, fout, audio_name)

    fout.close()
    

if __name__== "__main__":
  
    elan_to_html(file)
    
    print ('++ DONE ++')
