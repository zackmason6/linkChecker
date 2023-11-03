#!/usr/bin/python


"""

Version 4.7
Written by Zack Mason on 8/8/2023

Cleaned up encoding mess. Hit a bug with some encoding on website html files. Trying something
a bit different now.

----------------------------------------------------

Version 4.6
Written by Zack Mason on 7/19/2023

Implemented a false positive checker with some basic checks on a few false positive 
trends. These include redirects in DOI links and on the JSTOR website.

----------------------------------------------------

Version 4.5
Written by Zack Mason on 7/12/2023

Removed print statements and updated output.
----------------------------------------------------
Version 4.4
Written by Zack Mason on 7/11/2023

Implemented functionality to read in a list of URLs from a text file and ignore them if they 
are found in the URL checking process.

This still needs to be tested in the CoRIS Virtual Library checking function.
----------------------------------------------------

Version 3.3
Written by Zack Mason on 7/10/2023

Modified the output of functions 1 and 3 to print broken links as headers and then a subheading
containing a list of all affected files. 

Also added functions to replace large blocks of code that were being duplicated in both sections
1 and 3 of this application.

TO DO:

1. Read known false hits from a data file and mark them as links that should not be tested.
2. Check links against corresponding dictionaries before testing them. This should likely
   speed up the application as the link checker is probably testing a bunch of duplicates
   at the moment that it doesn't need to.

----------------------------------------------------

Version 3.2
Written by Zack Mason on 5/1/2023

Added functionality to print output to CSV files

python test-url.py -i <input directory or filepath> -f <functionality> -o <output file>
----------------------------------------------------

Version 3.1
Written by Zack Mason on 2/6/2023

Minor quality of life updates and formatting

----------------------------------------------------

Version 3.0
Written by Zack Mason on 1/5/2023

Updated functionality to successfully parse through the xml metadata files in the coris 
metadata library.

Added Command line input functionality for switching between script functions. The current
usage for this application would be something like this (note that you can substitute the
numbers 1, 2, or 3 in place of <functionality> to implement different functionality)

python test-url.py -i <input directory or filepath> -f <functionality>

Command Line Functionality Options:
- 1 - Website
- 2 - Virtual Library
- 3 - Metadata Library

Now requires the user to specify input directory or filepath as part of their command line input.
MAKE SURE YOU ENTER AN INPUT DIRECTORY OR FILEPATH! THIS WILL NOT WORK WITHOUT THAT INPUT

------------------------------------------------------------------------------------------------
Version 2.0
Written by Zack Mason on 12/21/2022

Updated functionality to successfully parse html files
Updated functionality to successfully parse coris virtual library xml

This thing is a mess. Apologies for the almost entire lack of comments. I'm working on it.

This script has all but been rewritten in this version. The basic idea of it being a link
checker is really all that remains. I haven't removed the old code just yet and I am actually
reusing the get_text method but even that has been rewritten to the point of it being basically
unrecognizable.

This script currently will check all links found in any and all html files in your current 
working directory and any subdirectories.

Once a list of html files is created, the script will read one into memory. It will then
parse that using htmlParser and grab any href a tags. These tags are then written to a
temporary file in the working directory. A processing function is then called that reads
this temporary file and processes each line to ensure the data are in the proper format.
In addition to some very basic checks of whether or not the line in question could be a
URL, it adds a base url to anything that looks like a relative link. This base url is
meant to be fed to the function as a parameter.

Once each line is processed, it is written to a second temporary file. This file is
then read and each link is tested. If the link returns an error code it is recorded
with the link and the location of the html file that the link was grabbed from into
a dictionary.

This dictionary of links and accompanying information is then appended to a master
dictionary and the entire loop keeps running until all html files in the list have
been processed accordingly. The master dictionary is then printed to standard output.

In addition to parsing through any html, this application is also designed to specifically
parse through the coris virtual library xml file. With some small tweaks it could really
parse through most xml files but because the virtual library contains many different entries
within one large xml file I thought it would just be easier to code in some of the tags I 
was looking for.

To parse through the xml, the application looks for the coris tags. It then identifies 
any text within each sub tag that starts with "http." I believe all of the links in this
document start with http. If this is wrong, I will adjust.

------------------------------------------------------------------------------------------

TO DO

1. SORT OUTPUT BASED ON ERROR
    1a. This only has to be done once per type (xml library, html) - make different data structures for high, medium, low priority errors.
    1b. Will need to make a list of error codes so you can build a switch.

2. 

"""

## Version 1.0.0 ##
## Written by Zack Mason on 10/16/2020 ##

## This program is used to check the urls in a certain file.
## Currently the path to the file is hardcoded. This should be
## changed. The user should be asked which file the urls are in.
## Additionally, it might be a good idea to structure the regex
## based around user input. Maybe. 
## This program takes all urls that match a regular expression and
## extracts them to another file. It then tests each url and returns
## the code associated with the test outcome.

import requests
from urllib.request import urlopen, Request
import urllib.request
import urllib
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
import os
import ssl
import certifi
import contextvars
import sys
import getopt
import argparse
import csv
import chardet
from ftplib import FTP

# The path below is where the file that contains links to not be tested is stored.
ignoreFilePath = '/nodc/projects/coris/ignoreThis.txt'
testedUrls = {}

class MyHTMLParser(HTMLParser):

  def handle_starttag(self, tag, attrs):
    try:
      tempOutput = "tempHTML.txt"
    except:
      tempOutput = "tempHTML2.txt"
    with open(tempOutput,"a") as f:
      # Only parse the 'anchor' tag.
      if tag == "a":
      # Check the list of defined attributes.
        for name, value in attrs:
      # If href is defined, print it.
          if name == "href":
          #print (name, "=", value)
            f.write(str(value)+"\n")

def test_ftp(myLink):
  try:
    hostNameList = re.findall(r"ftp\.[^\/]*",myLink)
    hostName = str(hostNameList[0])
    ftp = FTP(hostName)
    ftp.login()
    ftp.quit()
    return False
  except:
    return True

def checkForFalsePositives(linkToBeChecked,errorCode):
  """
  This is where all the quick-fixes for weird idiosyncracies will go.
  For example, journal websites don't seem to like the link checker bot
  so we will need to go ahead and assume that most of the journal links
  that get rejected as forbidden are likely not broken.
  """
  # Quick fix for DOIs 
  if ("doi" in str(linkToBeChecked) or "jstor" in str(linkToBeChecked)) and "403" in str(errorCode):
    isThisLinkBroken = False

  # Check for NCEI archive links with redirects
  elif ("nodc.noaa.gov" in str(linkToBeChecked) and "accession" in str(linkToBeChecked)) and "302" in str(errorCode):
    isThisLinkBroken = False
  else:
    #print("NOT A FALSE POSITIVE. ACTUALLY BROKEN.")
    isThisLinkBroken = True
  
  return isThisLinkBroken

def findEncoding(inputFile):
  try:
    result = chardet.detect(inputFile)
    charenc = result['encoding']
    tempFileObject = open(inputFile,"r", encoding=charenc)
    data = tempFileObject.read()
    tempFileObject.close()
  except:
    try:
      tempFileObject = open(inputFile,"r", encoding='utf-8')
      data = tempFileObject.read()
      tempFileObject.close()
    except:
      try:
        tempFileObject = open(inputFile,"r", encoding='latin1')
        data = tempFileObject.read()
        tempFileObject.close()
      except:
        tempFileObject = open(inputFile,"r", encoding='cp-1252')
        data = tempFileObject.read()
        tempFileObject.close()
  return data

def parseVirtualLibraryXML(inputFile):
  brokenLinks = {}
  #counter = 0
  data = findEncoding(inputFile)
  myroot = ET.fromstring(data)
  for index in range(len(myroot)):
    for x in myroot[index]:
      if str(x.text).startswith("http"):
        try:
          errorCode = url_test(x.text)
        except Exception as e:
          errorCode = str(e)
        #counter +=1
        #print("NUMBER OF LINKS PROCESSED: " + str(counter))
        if errorCode is not None:
          try:
            #print("\nCHEKCING THIS LINK: " + str(x.text) + " and this error code: " + str(errorCode))
            isThisReallyBroken = checkForFalsePositives(str(x.text),str(errorCode))
          except:
            isThisReallyBroken = True
          if (isThisReallyBroken == True):
            title = myroot[index].find('Title').text
            bibTextID = myroot[index].find('Local-number').text
            #print("\nBroken URL: " + x.text + "\n" + "Publication title: " + title + "\n" + "bibText ID: " + bibTextID + "\n" + "Error Code: " + str(errorCode))
            myDict = {title:{"Broken URL":x.text, "bibText ID":bibTextID, "Error Code":errorCode}}
            brokenLinks.update(myDict)
  return brokenLinks

def checkMetadataRecords(metadataPath):
  try:
    tempOutput = "tempHTML.txt"
  except:
    tempOutput = "tempHTML2.txt"
  #tempOutput = "tempHTML.txt"
  brokenLinks = {}
  #tagList = ["<browsen>","<networkr>","<onlink>","cormdlk"]
  listOfFiles = getFileList("xml",metadataPath)
  for metadataFile in listOfFiles:
    #print("\nCHEKCING THIS FILE: " + str(metadataFile))
    #singleFileDict = {metadataFile:{}}
    singleFileUrlList = parseXML(metadataFile)
    f = open(tempOutput, "w") # Clear temp output file
    f.close()
    with open(tempOutput,"a") as f:
      for singleUrl in singleFileUrlList:
        f.write(str(singleUrl)+"\n")
    singleFileBrokenLinks = get_text(tempOutput,metadataFile)
    #print("SINGLE FILE DICT LISTED HERE: " + str(singleFileBrokenLinks))
    brokenLinks = buildDictionary(brokenLinks, singleFileBrokenLinks)
  return brokenLinks

def processInput(inputString,my_path,fileBeingRead):
  #removeThisString = "//nodc/web/www.coris/1.3/prod/htdocs"
  inputString = inputString.strip()
  currentDirectoryName = re.sub("\/[^\/]*?\.html$","",fileBeingRead)
  if " " in inputString:
    inputString = inputString.replace(" ","%20")
  if "'" in inputString:
    inputString = inputString.replace("'","")
  print(str(inputString))
  
  if inputString.startswith("http") == True: # If the url or path looks like a URL, go ahead and return it.
    return inputString
  elif inputString.startswith("ftp") == True:
    return inputString
  if "crcp" in os.getcwd():
    return ""
  else: # If it looks like a relative link/path, we need to do some processing
    inputString = inputString.replace("\\","/")
    if inputString.startswith("#") == False: # If it doesn't start with http or a hashtag:
      if inputString.startswith("/") == False: # No http, no hashtag and no slash:
        if "mailto" in inputString: # Check if this is a mailto link
          return ""
        else: # if it isn't a mailto link:     # monitoring/welcome.html
          abbreviatedPath = re.sub(".+htdocs\/", "", currentDirectoryName) # Removes the beginning of the filepath
          if abbreviatedPath.endswith("htdocs") == False:
            adjustedBaseURL = baseURL + "/" + abbreviatedPath # Adds www.coris + / + filepath after htdocs
          else:
            adjustedBaseURL = baseURL
          inputString = adjustedBaseURL + "/" + inputString # Adds the path that was grabbed in inputString
          return inputString

      elif inputString.startswith(".."):
        inputString = inputString.replace("..","")
        relativeLinkResolved = re.sub("\/[^\/]*\/[^\/]*html$","",fileBeingRead)
        abbreviatedPath = re.sub(".+htdocs\/", "", relativeLinkResolved)
        revisedLink = baseURL + "/" + abbreviatedPath + inputString 
        return revisedLink

      elif inputString == "/":
        currentDirectoryName = re.sub("\/[^\/]*?\.html$","",fileBeingRead)
        abbreviatedPath = re.sub(".+htdocs\/", "", currentDirectoryName)
        adjustedBaseURL = baseURL + "/" + abbreviatedPath
        return adjustedBaseURL

      else: # This block means it does start with a "/"
        relativeLinkResolved = re.sub("[^\/]*\/[^\/]*html$","",fileBeingRead)
        abbreviatedPath = re.sub(".+htdocs\/", "", relativeLinkResolved)
        revisedLink = baseURL + "/" + abbreviatedPath + inputString
        myURL = baseURL + inputString
        return myURL

    else:
      inputString = ""
    return inputString

def getFileList(fileExtension, myPath):
  myFileList = []
  for root, dirnames, filenames in os.walk(myPath):
    #print(str(root))
    #print(str(filenames))
    for name in filenames:
      if name.endswith(fileExtension):
        myFilePath = os.path.join(root, name)
        myFileList.append(myFilePath)
  myFileList = list(set(myFileList))
  return myFileList

def buildDictionary(brokenLinks, singleFileBrokenLinks):
  if len(brokenLinks)<1: # CHECKS TO SEE IF MASTER DICTIONARY EXISTS. IF NOT, CREATES IT WITH THE CURRENT SINGLE FILE DICTIONARY
    #print("\nBROKEN LINKS DICTIONARY NOT FOUND. CREATING IT NOW.")
    for brokenURL in singleFileBrokenLinks:
      singleFileBrokenLinks[brokenURL]["Affected Files"] = list(set(singleFileBrokenLinks[brokenURL]["Affected Files"]))
    brokenLinks = singleFileBrokenLinks
  else:
    for brokenURL in singleFileBrokenLinks: # CHECKS EACH ENTRY IN THE SINGLE FILE DICTIONARY TO SEE IF THAT LINK IS IN THE MASTER DICTIONARY
      #print("\nCHECKING TO SEE IF " + str(brokenURL) +" is in the master dictionary...")
      if brokenURL in brokenLinks.keys(): # IF THE LINK IS IN THE MASTER DICTIONARY, check to see if the file is in affected files
        #print("THIS URL WAS FOUND IN THE MASTER DICTIONARY ALREADY")
        affectedFile = singleFileBrokenLinks[brokenURL]["Affected Files"][0]
        if len(affectedFile)>1:
          #print("AFFECTED FILE FROM SINGLE FILE BROKEN LINKS: " + str(affectedFile))
          #print("LIST OF AFFECTED FILES IN MASTER DICT: " + str(brokenLinks[brokenURL]["Affected Files"]))
          if affectedFile not in brokenLinks[brokenURL]["Affected Files"]:
            brokenLinks[brokenURL]["Affected Files"].append(affectedFile)
            #print("FILE NOT YET IN BROKEN LINKS MASTER DICT. APPENDING NOW.")
          #else:
            #print("AFFECTED FILE ALREADY IN BROKEN LINKS MASTER DICT")
      else: # IF THE LINK IS NOT IN THE MASTER DICTIONARY, ADD IT
        brokenLinks.update({brokenURL:singleFileBrokenLinks[brokenURL]})
            #print("THIS LINK WAS NOT FOUND IN THE MASTER DICT. ADDING IT NOW.")
  return brokenLinks

def parseHTML(baseURL,my_path):
  trueFileList = []
  if len(my_path)<=1:
    my_path = os.getcwd()
  brokenLinks = {}
  #print("getFileList method starting")
  htmlFileList = getFileList("html",my_path)
  for item in htmlFileList:
    print(str(item))
    if "metadata/records" not in item:
      trueFileList.append(item)
  numberOfFiles = len(trueFileList)
  #print("Number of Files to Parse: " + str(numberOfFiles))
  count = 0
  for item in trueFileList: # FOR EVERY FILE IN LIST OF FILES:
    count +=1
    #print("Processing file number " + str(count) + " out of " + str(numberOfFiles))
    try:
      newTempFile = "processedHTML.txt" # DESIGNATE TEMP FILE TO STORE PROCESSED URLs
    except:
      newTempFile = "processedHTML2.txt"
    if "metadata/records" not in item: # IF METADATA/RECORDS NOT IN FILE PATH:
      try:
        htmlData = findEncoding(item)
        #print("1. encoding found")
      except:
        #print("BAD ENCODING NOT RESOLVED. USING DUMMY TAG FOR THIS FILE: " + str(item) +"\n" + "THIS ENCODING WAS FOUND: " + str(charenc))
        htmlData = '<a href="https://www.w3schools.com">This is just a test</a>'

      if isinstance(htmlData, (str)) == True: # IF READING THE HTML FILE WAS SUCCESSFUL
        #print("2. file read successfully")
        try:
          tempOutput = "tempHTML.txt"
          f = open(tempOutput, "w") # Clear temp output file
          f.close()
        except:
          tempOutput = "tempHTML2.txt"
          f = open(tempOutput, "w") # Clear temp output file
          f.close()
        processedFileObject = open(newTempFile,"w")
        processedFileObject.close()
        parser = MyHTMLParser() # DECLARE NEW INSTANCE OF HTMLPARSER
        parser.feed(str(htmlData)) # FEED HTML TEXT INTO THE PARSER. THIS WILL WRITE OUTPUT TO A tempHTML.txt file (in this case, f)
        #print("3. HTML PARSED")
        f = open(tempOutput,"r+") # OPEN PARSER OUTPUT AND READ IT
        lines = f.readlines()
        f.close()
      #processedFileObject = open(newTempFile,"a")
      with open(newTempFile, "a") as processedFileObject:
        for line in lines:
          #print(str(line))
          if len(line) >1: # IF THE LINE CONTAINS ANYTHING POTENTIALLY USEFUL
            processedInput = processInput(line,baseURL,item) # PROCESS AND FORMAT THE LINE
            if len(processedInput) >0:
              processedFileObject.write(processedInput+"\n") # PRINT THE PROCESSED OUTPUT TO A NEW FILE CONTAINING ONLY FORMATTED LINKS
        #print("4. Processed URLs written to file. Beginning URL testing")
      singleFileBrokenLinks = get_text(newTempFile,item) # TEST EACH URL AND GET A RESULTING DICTIONARY FOR EACH. CONTAINS PAGE FOUND ON AND ERROR STATUS
      # THIS IS NEW CODE 7.10.2023
      brokenLinks = buildDictionary(brokenLinks,singleFileBrokenLinks)
      #print("5. brokenLinks updated")
      f.close()
  return brokenLinks

def parseXML(filename):
  try:
    tagList = ["browsen","networkr","onlink","cormdlk"]
    xmlTree = ET.parse(filename)
    url_list = []
    for elem in xmlTree.iter():
        if elem.tag in tagList:
            myUrl = elem.text
            myUrl = str(myUrl).strip()
            url_list.append(myUrl)
  except:
    url_list = []
  return url_list
    

def url_test(myinput):
  """This function tests the url passed to it as myinput. It strips newline characters
and then returns the response or error code."""
  my_url = myinput.strip()

  try:
    #ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    #response = urllib.request.urlopen(my_url, context=ssl_context)

    #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    }
    response = urlopen(Request(my_url,headers=headers,method='GET'),timeout=30,cafile=certifi.where())
    if response.status != 200:
      print(response.status)
      return response
    else:
      return None
  except Exception as e: 
    if "CERTIFICATE_VERIFY_FAILED" in str(e) and ".gov" in str(my_url):
      try:
        context = ssl._create_unverified_context()
        response = urllib.urlopen(Request(my_url, context=context),timeout=30)
        if response.status != 200:
          print(response.status)
          return response
        else:
          return None
      except Exception as e: return e
    else:
      return e

## This function reads each line of the input file and sends it to the url_test function
## as a separate string.
def get_text(processedLinks, pathToFile):
  ignoreTheseLinks = []
  fileList = []
  brokenLinks = {}
  try:
    ignoreFile = open(ignoreFilePath, 'r') #OPEN FILE CONTAINING FORMATTED LINKS
    ignoreLines = ignoreFile.readlines()
    ignoreFile.close()
    for ignoreThisURL in ignoreLines:
      ignoreThisURL = ignoreThisURL.strip()
      ignoreTheseLinks.append(str(ignoreThisURL))
  except:
    print("No ignore file found.")

  uniqueLines = []
  file = open(processedLinks, 'r') #OPEN FILE CONTAINING FORMATTED LINKS
  lines = file.readlines()
  file.close()
  lines = list(set(lines))
  numberOfLines = len(lines)
  #print("Testing line by line now. This many lines: " + str(numberOfLines))
  for line in lines:
    isThisLinkBroken = False
    line = line.strip()
    if line in testedUrls.keys():
      urlCode = testedUrls[line]
      if urlCode is not None:
        isThisLinkBroken = True

    elif ((len(line)>1) and ("ftp" not in line) and (line not in ignoreTheseLinks) and (line not in testedUrls.keys())):
      urlCode = url_test(line)
      newUrlDict = {line:urlCode}
      testedUrls.update(newUrlDict)
      if urlCode is not None:
        isThisLinkBroken = checkForFalsePositives(line,urlCode)

    elif (("ftp" in line) and (line not in ignoreTheseLinks) and (line not in testedUrls.keys())):
      isThisLinkBroken = test_ftp(line)
      if isThisLinkBroken == True:
        urlCode = "Unknown FTP Error"
        
    if isThisLinkBroken == True:
      fileList.append(pathToFile)
      fileList = list(set(fileList))
      temp={line:{"Error Code": urlCode,"Affected Files":fileList}}
      brokenLinks.update(temp)
    #elif line in ignoreTheseLinks:
    #  print("\nThe following URL was not tested as it was found in the ignore file: " + str(line))
  return brokenLinks

def main(argv):
   inputPath = ''
   outputfile = ''
   opts, args = getopt.getopt(argv,"hi:o:f:",["ifile=","ofile="])
   for opt, arg in opts:
      if opt == '-h':
         print ('test-url.py -f <functionality> -i <inputPath> -o <outputfile>')
         sys.exit()
      elif opt in ("-i", "--ifile"):
         inputPath = arg
      elif opt in ("-o", "--ofile"):
         outputfile = arg
      elif opt == '-f':
          functionality = arg
   return (functionality, inputPath, outputfile)

def sendToFile(outputFile, field_names, myDict):
  """
  This is actually not used right now.
  """
  with open(outputFile, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames = field_names)
    writer.writeheader()
    writer.writerows(myDict)

def formatOutput(brokenLinks,outputFile):
  urlList = []
  errorCodeList = []
  affectedFileListofLists = []

  for linkDictionary in brokenLinks:
    linkAddress = str(linkDictionary).strip()
    errorCode = brokenLinks[linkDictionary]["Error Code"]
    affectedFiles = brokenLinks[linkDictionary]["Affected Files"]
    affectedFiles = list(set(affectedFiles))
    urlList.append(linkAddress)
    errorCodeList.append(errorCode)
    affectedFileListofLists.append(affectedFiles)

  for i in range(len(urlList)):
    print("\nBAD URL: " + str(urlList[i]) + "\n ERROR CODE: " + str(errorCodeList[i]) + "\n AFFECTED FILES: " + str(affectedFileListofLists[i]))
  with open(outputFile, 'w', newline='') as myfile:
    wr = csv.writer(myfile)
    wr.writerow(("Link Address", "Error Code", "Affected Files"))
    for i in range(len(urlList)):
      wr.writerow((urlList[i], errorCodeList[i], affectedFileListofLists[i]))
  try:
    os.remove("tempHTML.txt")
  except:
    os.remove("tempHTML2.txt")

"""
The following is the main block.

This will parse the incoming command line input and decide on which functionality to implement.
"""
if __name__ == "__main__":
    
    if len(sys.argv)>1:
        inputTuple = main(sys.argv[1:])
        functionality = inputTuple[0]
        #print("FUNCTIONALITY LISTED AS: " + str(functionality))
        inputPath = inputTuple[1]
        print("INPUT LISTED AS: " + inputPath)
        outputFile = inputTuple[2]
        print("OUTPUT FILE LISTED AS: " + str(outputFile))
    else:
        sys.exit("\nNo argument given. Exiting program\n")

    if str(functionality) == '1':
        """
        This block will go through the coris website and test all the links it finds there.
        """
        print("\nWebsite Link Report\n")
        myDirectory = os.getcwd()
        if "crcp" in myDirectory:
          baseURL = "https://www.coralreef.noaa.gov"
        else:
          baseURL = "https://www.coris.noaa.gov"
        #print("\nstarting parseHTML method")
        brokenLinks = parseHTML(baseURL,inputPath)
        #print("\nparseHTML function finished")
        formatOutput(brokenLinks,outputFile)
        #print("\nformatOutput function finished")
        try:
          os.remove("processedHTML.txt")
        except:
          os.remove("processedHTML2.txt")
    
    elif str(functionality) == '2':
        publicationTitleList = []
        urlList = []
        bibTextList = []
        errorCodeList = []

        print("\nVirtual Library Link Report\n")
        # The line below is all that is needed to parse the coris virtual library and check the links
        brokenLinks = parseVirtualLibraryXML(inputPath)
        for linkDictionary in brokenLinks:
          publicationTitle = str(linkDictionary)
          publicationTitleList.append(publicationTitle)
          print("\nPublication Title: " + publicationTitle)
          brokenURL = str(brokenLinks[linkDictionary]['Broken URL'])
          urlList.append(brokenURL)
          print(" Broken URL: " + brokenURL)
          bibTextID = str(brokenLinks[linkDictionary]['bibText ID'])
          bibTextList.append(bibTextID)
          print(" Bib Text ID: " + bibTextID)
          errorCode = str(brokenLinks[linkDictionary]['Error Code'])
          errorCodeList.append(errorCode)
          print(" Error Code: " + errorCode)

        with open(outputFile, 'w', newline='') as myfile:
          wr = csv.writer(myfile)
          wr.writerow(("Publication Title", "Bib Text ID", "Broken URL", "Error Code"))
          for i in range(len(urlList)):
            wr.writerow((publicationTitleList[i], bibTextList[i], urlList[i], errorCodeList[i]))

    elif str(functionality) == '3':
        affectedFileList = []
        urlList = []
        errorCodeList = []
        print("\nMetadata Library Link Report\n")
        # The Following block will test all links in the coris metadata library
        #metadataPath = "/nodc/projects/coris/Metadata/Records/latest"
        brokenLinks = checkMetadataRecords(inputPath)
        formatOutput(brokenLinks,outputFile)
        

    else:
        sys.exit("\nIncorrect syntax entered. Try specifying -h option to see proper usage. Exiting program\n")
