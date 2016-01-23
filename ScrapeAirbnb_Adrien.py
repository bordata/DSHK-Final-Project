
"""
Scraping Airbnb
"""

import mechanize
import cookielib
from lxml import html
import csv
import cStringIO
import codecs
from random import randint
from time import sleep
from lxml.etree import tostring

import sys  
from PyQt4.QtGui import *  
from PyQt4.QtCore import *  
from PyQt4.QtWebKit import * 

################Deals with java script issue
#Take this class for granted.Just use result of rendering.
class Render(QWebPage):  
  def __init__(self, url):  
    self.app = QApplication(sys.argv)  
    QWebPage.__init__(self)  
    self.loadFinished.connect(self._loadFinished)  
    self.mainFrame().load(QUrl(url))  
    self.app.exec_()  
  
  def _loadFinished(self, result):  
    self.frame = self.mainFrame()  
    self.app.quit()  
############

# Browser
br = mechanize.Browser()


#learned necessary configuration from
#http://stockrt.github.io/p/emulating-a-browser-in-python-with-mechanize/

# Allow cookies
cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)

# Browser options
br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)

# Follows refresh 0 but not hangs on refresh > 0
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
#specify browser to emulate
br.addheaders = [('User-agent',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

#######################################
#  Wrapper Functions    ###############
#######################################

def IterateMainPage(location_string, loop_limit):
    MainResults = []
    """
    input:
        location_string (string) - this is a location string that conforms to the
                                   pattern on airbnb for example,
                                   
        loop_limit (integer) -    this is the maximum number of pages you want to parse.

    output:
        list of dictionaries, with each list element corresponding to a unique listing

    This function iterates through the main listing pages where different properties
    are listed and there is a map, and collects the list of properties available along
    with the limited amount of information that is available in that page.  This function
    returns a list of dictionaries with each list element corresponding to a unique listing.
    Other functions will take the output from this function and iterate over them to explore
    the details of individual listings.
    """

    base_url = 'https://www.airbnb.com/s/'
    page_url = '?page='


    try:
        for n in range(1, loop_limit+1):
            print 'Processing Main Page %s out of %s' % (str(n), str(loop_limit))
            #Implement random time delay for scraping
            sleep(randint(0,2))
            current_url = ''.join([base_url, location_string, page_url, str(n)])
            MainResults += ParseMainXML(current_url, n)


    except:
        print 'This URL did not return results: %s ' % current_url

    print 'Done Processing Main Page'
    return MainResults




#######################################
#  Main Page    #######################
#######################################


def ParseMainXML(url= 'https://www.airbnb.com/s/Cambridge--MA--United-States', pg = 0):

    """
    input: url (string )

            this is the url for the type of listings you want to search.
            default is to use the generic url to search for listings
            in Cambridge, MA
    input: pg (integer)

            this is an integer corresponding to the page number, this is meant
            to be passed in by the wrapper function and collected in the dictionary.

    output: dict
    ------
    This funciton parses the main page with mulitple airbnb listings, and
    returns a list of dictionaries corresponding to the attributes found
    """
    n = 1
    ListingDB = []
    k = 0

    try:

        tree = html.fromstring(br.open(url).get_data())
        listings = tree.xpath('//div[@class="listing"]')
        

        
        for listing in listings:
            dat = {}
            dat['baseurl'] = url
            dat['Lat'] = listing.attrib.get('data-lat', 'Unknown')
            dat['Long'] = listing.attrib.get('data-lng', 'Unknown')
            dat['Title'] = listing.attrib.get('data-name', 'Unknown')
            dat['ListingID'] = listing.attrib.get('data-id', 'Unknown')
            dat['UserID'] = listing.attrib.get('data-user', 'Unknown')
            dat['Price'] = ''.join(listing.xpath('div//span[@class="h3 text-contrast price-amount"]/text()'))
            dat['PageCounter'] = n
            dat['OverallCounter'] = n * pg
            dat['PageNumber'] = pg

            ShortDesc = listing.xpath('//h3[@class="h5 listing-name text-truncate row-space-top-1"]')[k].attrib.get('title')

            if len(ShortDesc) > 0:
                dat['ShortDesc'] = ShortDesc

            if len(listing.xpath('div/div//span/i')) > 0:
                dat['BookInstantly'] = 'Yes'

            else:
                dat['BookInstantly']  = 'No'

            ListingDB.append(dat)
            n += 1
            k += 1

        return ListingDB

    except:
        print 'Error Parsing Page - Skipping: %s' % url
        #if there is an error, just return an empty list
        return ListingDB



#######################################
#  Detail Pages #######################
#######################################

def iterateDetail(mainResults):
    """
    This function takes the list of dictionaries returned by the
    IterateMainPage, and "enriches" the data with detailed data
    from the particular listing's info - if there is an error
    with getting that particular listing's info, the dictionary
    will be populated with default values of "Not Found"
    """
    finalResults = []
    counter = 0
    baseURL = 'https://www.airbnb.com/rooms/'
    
    mainResults = mainResults[:]
    
    for listing in mainResults:
        counter += 1
        print 'Processing Listing %s out of %s' % (str(counter), str(len(mainResults)))

        #Construct URL
        currentURL = ''.join([baseURL, str(listing['ListingID'])])

        #Get the tree
        tree = getTree(currentURL)

        #Parse the data out of the tree
        DetailResults = collectDetail(currentURL,tree, listing['ListingID'])

        #Collect Data
        newListing = dict(listing.items() + DetailResults.items())

        #Append To Final Results
        finalResults.append(newListing)

    return finalResults


def fixDetail(mainResults, indexList):

    finalResults = mainResults[:]
    baseURL = 'https://www.airbnb.com/rooms/'

  

    ######Only Modify This Part When You Want To Redo Certain Listings!!!###

    for i in indexList:
        print 'fixing index %s' % str(i)
        listingID = str(finalResults[i]['ListingID'])
        currentURL = ''.join([baseURL, listingID])

        #Get the tree
        tree = getTree(currentURL)

        #Parse the data out of the tree
        DetailResults = collectDetail(currentURL,tree, listingID)

        #Collect Data
        newListing = dict(finalResults[i].items() + DetailResults.items())

        #Append To Final Results
        finalResults[i] = newListing

    return finalResults


def getTree(url):
    """
    input
        url (string): this is a url string.  example: "http://www.google.com"

    output
        tree object:  will return a tree object if the url is found,
        otherwise will return a blank string
    """
    try:
        #Implement random time delay for scraping
        #sleep(randint(0,1))
        tree = html.fromstring(br.open(url).get_data())
        return tree

    except:
        #Pass An Empty String And Error Handling Of Children Functions Will Do
        #Appropriate Things
        print 'Was not able to fetch data from %s' % url
        return ''


def collectDetail(url,treeObject, ListingID):
    Results = {'AboutListing': 'Not Found',
                     'HostName': 'Not Found',
                     'MemberDate': 'Not Found',
                     'R_acc' : 'Not Found',
                     'R_comm' : 'Not Found',
                     'R_clean' : 'Not Found',
                     'R_loc': 'Not Found',
                     'R_CI' : 'Not Found',
                     'R_val' : 'Not Found',
                     'R_rev' : 'Not Found',
                     'P_ExtraPeople' : 'Not Found',
                     'P_Cleaning' : 'Not Found',
                     'P_Deposit' : 'Not Found',
                     'P_Weekly' : 'Not Found',
                     'P_Monthly' : 'Not Found',
                     'Cancellation' : 'Not Found',
                     'A_Kitchen' : 0,
                     'A_Internet' : 0,
                     'A_TV' : 0,
                     'A_Essentials' : 0,
                     'A_Shampoo' : 0,
                     'A_Heat' : 0,
                     'A_AC' : 0,
                     'A_Washer' : 0,
                     'A_Dryer' : 0,
                     'A_Parking' : 0,
                     'A_Internet' : 0,
                     'A_CableTV' : 0,
                     'A_Breakfast' :  0,
                     'A_Pets' : 0,
                     'A_FamilyFriendly' : 0,
                     'A_Events' : 0,
                     'A_Smoking' : 0,
                     'A_Wheelchair' : 0,
                     'A_Elevator' : 0,
                     'A_Fireplace' : 0,
                     'A_Intercom' : 0,
                     'A_Doorman' : 0,
                     'A_Pool' : 0,
                     'A_HotTub' : 0,
                     'A_Gym' : 0,
                     'A_SmokeDetector' : 0,
                     'A_CarbonMonoxDetector' : 0,
                     'A_FirstAidKit' : 0,
                     'A_SafetyCard' : 0,
                     'A_FireExt' : 0,
                     'S_PropType' : 'Not Found',
                     'S_Accomodates' : 'Not Found',
                     'S_Bedrooms' : 'Not Found',
                     'S_Bathrooms' : 'Not Found',
                     'S_NumBeds' : 'Not Found',
                     'S_BedType' : 'Not Found',
                     'S_CheckIn' : 'Not Found',
                     'S_Checkout' : 'Not Found'
                     }

    try:
        #
        ###################
        Results['AboutListing'] = getAboutListing(treeObject, ListingID)
        Space = getSpaceInfo(treeObject, ListingID)
        Results['S_PropType'] = Space['PropType']
        Results['S_Accomodates'] = Space['Accommodates']
        Results['S_Bedrooms'] = Space['Bedrooms']
        Results['S_Bathrooms'] = Space['Bathrooms']
        Results['S_NumBeds'] = Space['NumBeds']
        Results['S_BedType'] = Space['BedType']
        Results['S_CheckIn'] = Space['CheckIn']
        Results['S_Checkout'] = Space['CheckOut']



        
        ####################
        Results['HostName'] = getHostName(treeObject, ListingID)
        Results['MemberDate'] = getMemberDate(treeObject, ListingID)

        #accuracy, communication, cleanliness, location, checkin, value, reviews
        Results['R_acc'], Results['R_comm'], Results['R_clean'], Results['R_loc'], \
        Results['R_CI'], Results['R_val'],Results['R_rev'] = getTheStars(treeObject, ListingID)

        #price
        PriceData = getPriceInfo(treeObject, ListingID)
        Results['P_ExtraPeople'] = PriceData['ExtraPeople']
        Results['P_Cleaning'] = PriceData['CleaningFee']
        Results['P_Deposit'] = PriceData['SecurityDeposit']
        Results['P_Weekly'] = PriceData['Weeklydiscount']
        Results['P_Monthly'] = PriceData['Monthlydiscount']
        Results['Cancellation'] = PriceData['Cancellation']

        #Amenities
        Am = getAmenities(url, ListingID)
        Results['A_Kitchen'] = Am['Kitchen']
        Results['A_Internet'] = Am['Internet']
        Results['A_TV'] = Am['TV']
        Results['A_Essentials'] = Am['Essentials' ]
        Results['A_Shampoo'] = Am['Shampoo']
        Results['A_Heat'] = Am['Heating']
        Results['A_AC'] = Am['Air Conditioning']
        Results['A_Washer'] = Am['Washer']
        Results['A_Dryer'] = Am['Dryer']
        Results['A_Parking'] = Am['Free Parking on Premises']
        Results['A_Internet'] = Am['Wireless Internet']
        Results['A_CableTV'] = Am['Cable TV' ]
        Results['A_Breakfast'] =  Am['Breakfast']
        Results['A_Pets'] = Am['Pets Allowed']
        Results['A_FamilyFriendly'] = Am['Family/Kid Friendly']
        Results['A_Events'] = Am['Suitable for Events']
        Results['A_Smoking'] = Am['Smoking Allowed']
        Results['A_Wheelchair'] = Am['Wheelchair Accessible']
        Results['A_Elevator'] = Am['Elevator in Building']
        Results['A_Fireplace'] = Am['Indoor Fireplace' ]
        Results['A_Intercom'] = Am['Buzzer/Wireless Intercom']
        Results['A_Doorman'] = Am['Doorman']
        Results['A_Pool'] = Am['Pool']
        Results['A_HotTub'] = Am['Hot Tub']
        Results['A_Gym'] = Am['Gym']
        Results['A_SmokeDetector'] = Am['Smoke Detector']
        Results['A_CarbonMonoxDetector'] = Am['Carbon Monoxide Detector']
        Results['A_FirstAidKit'] = Am['First Aid Kit' ]
        Results['A_SafetyCard'] = Am['Safety Card']
        Results['A_FireExt'] = Am['Fire Extinguisher']
        return Results

    except:
        #Just Return Initialized Dictionary
        return Results



#############################################
### #########################

def getHostName(tree, ListingID):
  
    host_name = 'Not Found'

    try:
        host_name = tree.xpath('//a[@class="link-reset text-wrap"]')[0].text
        return host_name

    except:
        print 'Unable to parse host name for listing id: %s' % str(ListingID)
        return host_name


def getMemberDate(tree, ListingID):
    
    membership_date = 'Not Found'

    try:
        membership_date=tree.xpath('//div[@class="row row-condensed space-2"]//span')[0].text
        membership_date = membership_date.replace("Member since", "")
        membership_date=membership_date.strip()
        
        return membership_date

    except:
        print 'Unable to parse membership date for listing id: %s' % str(ListingID)
        return membership_date


def getTheStars(tree,ListingID):
    """
    input: xmltree object
    output: list of stars
    -----------------
   return list of stars for Accuracy,Communication,Cleanliness,Check In,Value,#reviews
    """
    reviews= tree.xpath('//div[@class="star-rating-wrapper"]/span[@class="h6"]//span')[1].text 
    
    try:
        #Get Nodes That Contain The Grey Text, So That You Can Search For Sections
        elements = tree.xpath('//div[@class="col-lg-6"]//strong')

        
        for element in elements:

            if element.text.find('Accuracy') >= 0:
                #If you find what you are looking for Go Up One Level Then Go Sideways
                targetelement = element.getprevious()
                accuracy = targetelement.getchildren()[0].getchildren()[0].get('content')
        
            if element.text.find('Communication') >= 0:
                targetelement = element.getprevious()
                communication = targetelement.getchildren()[0].getchildren()[0].get('content')
        
            if element.text.find('Cleanliness') >= 0:
                targetelement = element.getprevious()
                cleanliness = targetelement.getchildren()[0].getchildren()[0].get('content')
        
            
            if element.text.find('Location') >= 0:
                targetelement = element.getprevious()
                location = targetelement.getchildren()[0].getchildren()[0].get('content')
        
            if element.text.find('Check In') >= 0:
                targetelement = element.getprevious()
                checkin = targetelement.getchildren()[0].getchildren()[0].get('content')
        
            
            if element.text.find('Value') >= 0:
                targetelement = element.getprevious()
                value = targetelement.getchildren()[0].getchildren()[0].get('content')
        
        return accuracy,communication,cleanliness,location,checkin,value,reviews
   
    except:
        print 'Unable to parse stars listing id: %s' % str(ListingID)
        return accuracy,communication,cleanliness,location,checkin,value,reviews
   
########################################
##  ####################

def getAboutListing(tree, ListingID):
    """
    input: xmltree object
    output: string
    -----------------
    This function parses an individual listing's page to find
    the "About This Listing" and extracts the associated text
    """
    try:
    #Go To The Panel-Body
        elements = tree.xpath('//h4[@class="space-4 text-center-sm"]/span')

        #Search For "About This Listing" In Elements
        for element in elements:
            if element.text.find('About this listing') >= 0:
                #When You Find, it return the text that comes afterwards
                return element.getparent().getnext()[0].xpath('.//span')[0].text

    except:
        print 'Error finding *About Listing* for listing ID: %s' % ListingID
        return 'No Description Found'


def getSpaceInfo(tree, ListingID = 'Test'):

    """
    input: xmltree object
    output: dict
    -----------------
    This function parses an individual listing's page to find
    the all of the data in the "Space" row, such as Number of
    Bedrooms, Number of Bathrooms, Check In/Out Time, etc.
    """
    #Initialize Values
    dat = {'PropType': 'Not Found', 'Accommodates': 'Not Found',
           'Bedrooms': 'Not Found', 'Bathrooms' : 'Not Found',
           'NumBeds': 'Not Found', 'BedType': 'Not Found',
           'CheckIn': 'Not Found', 'CheckOut': 'Not Found'}

    try:
        #Get Nodes That Contain The Grey Text, So That You Can Search For Sections
        elements = tree.xpath('//div[@class="row"]/div[@class="col-md-3 text-muted"]/span')

          #find The space portion of the page,
        #then go back up one level and sideways one level
        for element in elements:

            if element.text.find('The Space') >= 0:
                #If you find what you are looking for Go Up One Level Then Go Sideways
                targetelement = element.getparent().getnext()
                break

        #Depth - First Search of The Target Node
        descendants = targetelement.iterdescendants()

        for descendant in descendants:
            #check to make sure there is text in descendant
            if descendant.text:
                ##Find Property Type##
                if descendant.text.find('Property type:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')

                    if len(prop) >= 1:
                        dat['PropType'] = prop[0].text

                ##Find Accomodates ####
                if descendant.text.find('Accommodates:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['Accommodates'] = prop[0].text

                ##Find Bedrooms ####
                if descendant.text.find('Bedrooms:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['Bedrooms'] = prop[0].text

                ##Find Bathrooms ####
                if descendant.text.find('Bathrooms:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['Bathrooms'] = prop[0].text

                ##Find Number of Beds ####
                if descendant.text.find('Beds:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['NumBeds'] = prop[0].text

                ##Find Bed Type ####
                if descendant.text.find('Bed type:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['BedType'] = prop[0].text

                ##Find Check In Time ####
                if descendant.text.find('Check In:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['CheckIn'] = prop[0].text

                ##Find Check Out Time ####
                if descendant.text.find('Check Out:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['CheckOut'] = prop[0].text
        return dat

    except:
        print 'Error in getting Space Elements for listing iD: %s' % str(ListingID)
        return dat

#######################################
#  Xi's Functions #####################
#######################################

def getPriceInfo(tree, ListingID):
    """
    input: xmltree object
    output: dict
    -----------------
    This function parses an individual listing's page to find
    the all of the data in the "Price" row, such as Cleaning Fee, Security Deposit, Weekly discount, etc.
    """
    #Initialize Values
    dat = {'ExtraPeople': 'Not Found', 'CleaningFee': 'Not Found', 'SecurityDeposit': 'Not Found',
       'Weeklydiscount': 'Not Found','Monthlydiscount': 'Not Found','Cancellation' : 'Not Found'}

    try:
        #Get Nodes That Contain The Grey Text, So That You Can Search For Sections
        elements = tree.xpath('//div[@class="row"]/div[@class="col-md-3 text-muted"]/span')

          #find The price portion of the page,
          #then go back up one level and sideways one level
        for element in elements:

            if element.text.find('Prices') >= 0:
                #If you find what you are looking for Go Up One Level Then Go Sideways
                targetelement = element.getparent().getnext()
                break

        #Depth - First Search of The Target Node
        descendants = targetelement.iterdescendants()

        for descendant in descendants:
            #check to make sure there is text in descendant
            if descendant.text:
                ##Find Extra People Free ##
                if descendant.text.find('Extra people:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['ExtraPeople'] = prop[0].text

                ##Find Cleaning Fee ####
                if descendant.text.find('Cleaning Fee:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['CleaningFee'] = prop[0].text

                ##Find Security Deposit ####
                if descendant.text.find('Security Deposit:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['SecurityDeposit'] = prop[0].text

                ##Find Weekly Price ####
                if descendant.text.find('Weekly discount:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['Weeklydiscount'] = prop[0].text

                ##Find Monthly Price ####
                if descendant.text.find('Monthly discount:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['Monthlydiscount'] = prop[0].text

                ##Find Cancellation ####
                if descendant.text.find('Cancellation:') >= 0:
                    prop =  descendant.getparent().xpath('.//strong')
                    if len(prop) >= 1:
                        dat['Cancellation'] = prop[0].text
        return dat

    except:
        print 'Error in getting Space Elements for listing iD: %s' % str(ListingID)
        return dat

#########################################
#  Amenities ############################
#########################################
def getAmenitiesList(url, ListingID):
    """
    input: url
    output: list of available amenities
    -----------------
    This function parses an individual listing's page to find
    the amenities available in the listing.  The amenities that are available
    are collected into a list.
    """
    amenities = []

    try:
        r = Render(url)  
        result = r.frame.toHtml()
        target = html.fromstring(str(result.toAscii()))

        amenities= target.xpath('//*[@class="expandable-content expandable-content-full"]')[0].xpath('.//span/strong/text()')
        
        return amenities

    except:
        print 'Error in getting amenities for listing iD: %s' % str(ListingID)
        return amenities

def getAmenities(url, ListingID):
    """
    input: xmltree object
    output: dict of binary indication if amenity exists or not
    -----------------
    This function parses an individual listing's page to find
    the amenities available in the listing.  The amenities that are available
    are collected into a list.
    """

       #Initialize Values
    dat = {'Kitchen': 0, 'Internet': 0, 'TV': 0, 'Essentials' : 0,
           'Shampoo': 0, 'Heating': 0, 'Air Conditioning': 0, 'Washer': 0,
           'Dryer': 0, 'Free Parking on Premises': 0,
           'Wireless Internet': 0, 'Cable TV' : 0,'Breakfast': 0, 'Pets Allowed': 0,
           'Family/Kid Friendly': 0, 'Suitable for Events': 0,
           'Smoking Allowed': 0, 'Wheelchair Accessible': 0,
           'Elevator in Building': 0, 'Indoor Fireplace' : 0,
           'Buzzer/Wireless Intercom': 0, 'Doorman': 0,
           'Pool': 0, 'Hot Tub': 0, 'Gym': 0,'Smoke Detector': 0,
           'Carbon Monoxide Detector': 0, 'First Aid Kit' : 0,
           'Safety Card': 0, 'Fire Extinguisher': 0}

    amenities = getAmenitiesList(url, ListingID)

    for amenity in dat.keys():
        if amenity in amenities:
            dat[amenity] = 1

    return dat

######################################
#### Save Results ####################

class DictUnicodeWriter(object):

    def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, D):
        self.writer.writerow({k:v.encode("utf-8") if isinstance(v, unicode) else v for k,v in D.items()})
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for D in rows:
            self.writerow(D)

    def writeheader(self):
        self.writer.writeheader()

def writeToCSV(resultDict, outfile):

    colnames = [ 'ListingID', 'Title','UserID','baseurl',  'Price', \
        'AboutListing','HostName', 'MemberDate', 'Lat','Long','BookInstantly','Cancellation',  \
        'OverallCounter','PageCounter','PageNumber', \
         'A_AC','A_Breakfast','A_CableTV','A_CarbonMonoxDetector','A_Doorman','A_Dryer','A_TV', \
         'A_Elevator','A_Essentials','A_Events','A_FamilyFriendly','A_FireExt','A_Fireplace','A_FirstAidKit', \
         'A_Gym','A_Heat','A_HotTub','A_Intercom','A_Internet','A_Kitchen','A_Parking','A_Pets','A_Pool','A_SafetyCard', \
         'A_Shampoo','A_SmokeDetector','A_Smoking','A_Washer','A_Wheelchair', \
         'P_Cleaning','P_Deposit','P_ExtraPeople','P_Monthly','P_Weekly', \
         'R_CI','R_acc','R_clean','R_comm', \
         'R_loc','R_val','R_rev', \
         'S_Accomodates','S_Bathrooms','S_BedType','S_Bedrooms', \
         'S_CheckIn','S_Checkout','S_NumBeds','S_PropType','ShortDesc']

    with open(outfile, 'wb') as f:
        w = DictUnicodeWriter(f, fieldnames=colnames)
        w.writeheader()
        w.writerows(resultDict)

#######################################
#  Testing ############################
#######################################

if __name__ == '__main__':

    #Iterate Through Main Page To Get Results
    MainResults = IterateMainPage('Hongkong', 1)

    #Take The Main Results From Previous Step and Iterate Through Each Listing
    #To add more detail
    DetailResults = iterateDetail(MainResults)

    #NewRes = fixDetail(MainResults, [0,1])

    #Write Out Results To CSV File, using function I defined
    #writeToCSV(NewRes,'FixedOutput.csv')
    writeToCSV(DetailResults, 'Output.csv')
    #writeToCSV(MainResults, 'Output.csv')
    