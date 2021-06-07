# googlebookextractor

## Synopsis

- Converts a google play book page body element to plan text
 
## Overview

The Google Books Reader GUI is nice for casual reading. However, the reader's search functionality is limited for gathering data for research. It would be better if we could use regular expressions for searching but the GUI does not support this feature. To get around this, the text rendered in the reader could be copied into a text file. Because the reader's GUI does not explicitly support copying and pasting the text, this script was created to convert the contents of the reader's html body element to plain text. This allows us to obtain the plain text version of the text currently rendered in the reader. 

## Requirements

- Python 3
- lxml
- re
- argparse
- Google or FireFox to retrieve the html body element

## Example

1) Open a google ebook from the reader url. https://play.google.com/books/reader?id={YOURBOOKID}

2) With an ebook opened in the reader, open the developer tools and navigate to the body element found inside the first iframe and copy the element. 

3) Paste this element into a new xml file. 

4) Execute the following command to extract the plain text version of text in the reader and save to a text file. 

```
$python googlebookextractor.py --munge ".\Example\Example_0.xml" > Example_0.txt
```

If the file needs to be reextracted you can remove the "--munge" command

```
$python googlebookextractor.py ".\Example\Example_0_Munged.xml" > Example_0.txt
```

## Additional Notes:

- Munging the file will:
        - Add a body element tag around the html element, 
        - Remove form, br, and input elements since they do not have closing tags 
            - Closing tags required for xml parsing by lxml.
            - Probably could have used an html parser in retrospect...
    - Only need to invoke the "--munge" flag if the file has not already been munged. 
    - Limitations: 
        - The input file must contain a specific inner html body element
        - To obtain the correct html body element, the display options in the Google Books gui must have the following set: "View: 'Flowing text', Page Layout:'Two-page layout'
        - The inner html body element only contains the contents of the currently rendered pages. Thereforexml files must be generated for all pages of the book. 
        - Script can only process one xml file at a time. 
            - A List item that is a continuation of a list item on a previous file will be interpreted as a new list item. So this will need to be manually fixed.
            - A paragraph that is a continuation of a paragraph on a previous file will be interpreted as a new paragraph. So this will need to be manually fixed.