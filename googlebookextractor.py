'''
Synopsis: 
 
 - Converts a google play book page body element to plan text

Requirements: 
    - Python 3
    - lxml
    - re
    - argparse

Additional Notes: 
    - Munging the file will:
        - Add a body element tag around the html element, 
        - Remove form, br, and input elements since they do not have closing tags 
            - Closing tags required for xml parsing by lxml.
            - Probably could have used an html parser in retrospect...
    - Only need to invoke the "--munge" flag if the file has not already been munged. 
    - Limitations: 
        - The input file must contain a specific inner html body element
        - To obtain the correct html body element, the display options in the Google Books gui
          must have the following set: "View: 'Flowing text', Page Layout:'Two-page layout'
        - The inner html body element only contains the contents of the currently rendered 
          pages. Thereforexml files must be generated for all pages of the book. 
        - Script can only process one xml file at a time. 
            - A List item that is a continuation of a list item on a previous file will
              be interpreted as a new list item. So this will need to be manually fixed.
            - A paragraph that is a continuation of a paragraph on a previous file will
              be interpreted as a new paragraph. So this will need to be manually fixed.
'''

from lxml import etree as ET
import re
import argparse

# Define arguments for CLI
parser = argparse.ArgumentParser(description='Converts a google play book page body element to plan text')
parser.add_argument('--munge', action='store_true',
                    help='Enables munging step to format inner html body element for parsing')
parser.add_argument('inputFile', metavar='f', type=str, #nargs='+',
                    help='Path of file containing body element')

def munge(filePath):
    ''' Munges the inner html body element for parsing by extract function
    
    keyArgs:
    filePath: Path to file that contains html inner body element that needs to be munged. 

    Notes: 
    This will overwrite the file in place
    '''
    readContents = ''
    with open(filePath, 'r', encoding='utf8') as f:
        readContents = f.read()
    
    readContents = '<body>{0}</body>'.format(readContents)
    readContents.replace('&nbsp;', ' ')
    readContents.replace('', ' ')
    readContents = re.sub(r'(&nbsp;)+', '', readContents)
    readContents = re.sub(r'.*<br.*', '', readContents)
    readContents = re.sub(r'.*<form>.*', '', readContents)
    readContents = re.sub(r'.*</form>.*', '', readContents)
    readContents = re.sub(r'.*<input.*', '', readContents)
    
    with open(filePath, 'w', encoding='utf8') as f:
         f.write(readContents)

def extract(filePath):
    ''' Extracts the contents of the google book page by parsing its corresponding inner html body element 
    
    keyArgs:
    filePath: Path to file that contains munged html body element that contains the desired text.
    '''
    outStr = ''
    rootXMLObj = ET.parse(filePath)
    gbsXMLObjList = rootXMLObj.xpath('//gbs')
    lastParentXMLObj = gbsXMLObjList[0]
    aElemFound = False
    onNewColumn = False
    liCount = 0
    for curGbsXMLObj in gbsXMLObjList:
        parentXMLObj = curGbsXMLObj.getparent()
        gbtXMLObjList = curGbsXMLObj.xpath('gbt')
        # Remove new line characters for paragraphs that continue to the second column on the currently rendered page
        if (rootXMLObj.getpath(curGbsXMLObj).split('table/tbody/tr/td')[1] != rootXMLObj.getpath(lastParentXMLObj).split('table/tbody/tr/td')[1]):
            outStr = outStr[:-2]
            onNewColumn = True
        # Capture text stored in a normal paragraph
        if parentXMLObj.tag == 'p':
            if len(gbtXMLObjList) > 1:
                if (lastParentXMLObj.tag == 'span' and lastParentXMLObj.attrib['class'] == 'i'):
                    for curGbtXMLObj in gbtXMLObjList:
                        if (curGbtXMLObj.text):
                            outStr += curGbtXMLObj.text
                        else:
                            outStr += ' '
                else:
                    # Only add the a tab if there wasn't an arbitrary line break caused by the "a" element
                    if not (aElemFound):
                        # Only add the tab if this is the start of a new paragraph. 
                        if not ('ocean-reopened-parent' in parentXMLObj.attrib):
                            outStr += '\t'
                    for curGbtXMLObj in gbtXMLObjList:
                        if (curGbtXMLObj.text):
                            outStr += curGbtXMLObj.text
                        else:
                            outStr += ' '
                outStr += '\n\n'
            else:
                # Create new lines seperating paragraphs
                for curGbtXMLObj in gbtXMLObjList:
                    if (curGbtXMLObj.text):
                        outStr += curGbtXMLObj.text
                    else:
                        outStr += '\n'
            liCount = 0
        # Capture italized text by surround text with "<i>" flags
        elif (parentXMLObj.tag == 'span' and parentXMLObj.attrib['class'] == 'i'):
            # remove last new line character if the italicized words are contained in a paragraph
            if (lastParentXMLObj.tag == 'p'):
                outStr = outStr[:-2]
            outStr += '<i>'
            for curGbtXMLObj in gbtXMLObjList:
                if (curGbtXMLObj.text):
                    outStr += curGbtXMLObj.text
                else:
                    outStr += ' '
            outStr += '</i>'
        # Capture Chapter headers
        elif (parentXMLObj.tag == 'span' and parentXMLObj.attrib['class'] == 'ac'):
            for curGbtXMLObj in gbtXMLObjList:
                if (curGbtXMLObj.text):
                    outStr += curGbtXMLObj.text.upper()
                else:
                    outStr += ' '
            outStr += '\n'   
        # Capture text stored in list
        elif parentXMLObj.tag == 'li':
            #print('liCount: {0}'.format(liCount))
            if (not aElemFound and not onNewColumn):
                outStr += '\t* '
            if (onNewColumn and 'value' in parentXMLObj.attrib):
                if int(parentXMLObj.attrib['value']) > liCount:
                    outStr += '\n\n\t* '
            for curGbtXMLObj in gbtXMLObjList:
                if (curGbtXMLObj.text):
                    outStr += curGbtXMLObj.text
                else:
                    outStr += ' '
            outStr += '\n\n'
            if (parentXMLObj != lastParentXMLObj):
                liCount += 1
        # Remove new line character for any occurence of "a" element (We don't know what the "a" element does in the original text)
        aElemXMLObjlist = parentXMLObj.xpath('a')
        if (aElemXMLObjlist):
            for curAElemXMLObj in aElemXMLObjlist:
                if parentXMLObj.index(curAElemXMLObj) == (parentXMLObj.index(curGbsXMLObj) + 1) and parentXMLObj.index(curAElemXMLObj) not in [0, len(parentXMLObj.getchildren()) - 1]:
                    outStr = outStr[:-2]
                    aElemFound = True
        else:
            aElemFound = False
        onNewColumn = False
        lastParentXMLObj = parentXMLObj
    return outStr

if __name__ == '__main__':
    args = parser.parse_args()
    if args.munge:
        munge(args.inputFile)
    try:
        print(extract(args.inputFile))
    except Exception as e:
        print('Contents of file "{0}" could not be extracted due to the following errors:'.format(args.inputFile))
        print(e)

## Dev Notes
# Copy the body inner html element 
# save it as an xml file. 
# readd body element as root element
# replace all &nbsp with spaces to handle lxml.etree.XMLSyntaxError: Entity 'nbsp' not defined
# Input elements need closing elements <input class="gb-pagecontrol-input" title="Page number"></form>