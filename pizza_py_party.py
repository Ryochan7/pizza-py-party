#!/usr/bin/env python

import os
import sys
import optparse
import re
import urllib2
import cookielib
from xml.dom import minidom as dom
import htmllib_adapter as htmllib
import formatter
from urllib import urlencode
from getpass import getpass

# Set up cookie management
cj = cookielib.LWPCookieJar ()
opener = urllib2.build_opener (urllib2.HTTPCookieProcessor (cj))
urllib2.install_opener (opener)

# Page Urls. Urls are typically references to previous pages visited.
# There are lots of them.
# Change in pages are dependent on the post data passed
# (via the goTo or _idcl variable depending on the page and method)
# TODO (ryochan7): Get rid of all non-essential urls. Grab urls from the action
#                  attribute in forms
TEST_ROOT = "https://order.dominos.com"
LOGIN_URL = urllib2.urlparse.urljoin (TEST_ROOT, "/olo/faces/login/login.jsp")
ADD_COUPON_URL = urllib2.urlparse.urljoin (TEST_ROOT, "/olo/faces/order/coupons.jsp")
BUILD_PIZZA_URL = urllib2.urlparse.urljoin (TEST_ROOT, "/olo/faces/order/step2_choose_pizza.jsp")
ADD_PIZZA_URL = urllib2.urlparse.urljoin (TEST_ROOT, "/olo/faces/order/step2_build_pizza.jsp")
ADD_SIDES_URL = ADD_PIZZA_URL
CHECKOUT_URL = urllib2.urlparse.urljoin (TEST_ROOT, "/olo/faces/order/step3_choose_drinks.jsp")
SUBMIT_ORDER_URL = urllib2.urlparse.urljoin (TEST_ROOT, "/olo/faces/order/placeOrder.jsp")
LOGOUT_URL = urllib2.urlparse.urljoin (TEST_ROOT, "/olo/servlet/init_servlet?target=logout")
CALCULATE_TOTAL_URL = urllib2.urlparse.urljoin (TEST_ROOT, "/olo/servlet/ajax_servlet")
#LOGIN_URL = "https://order.dominos.com/olo/faces/login/login.jsp"
#LOGIN_URL = "https://www01.order.dominos.com/olo/faces/login/login.jsp"
#CALCULATE_TOTAL_URL = "https://www01.order.dominos.com/olo/servlet/ajax_servlet"
CALCULATE_TOTAL_URL_POST_VARS = {
    "cmd": "priceOrder",
    "formName": "orderSummaryForm:",
    "getFreeDeliveryOffer": "N",
    "runCouponPicker": "N",
    "runPriceOrder": "Y",
}
#SUBMIT_ORDER_URL = "https://www01.order.dominos.com/olo/faces/order/placeOrder.jsp"
#LOGOUT_URL = "http://www01.order.dominos.com/olo/servlet/init_servlet?target=logout"


#LOGIN_URL = "https://www01.order.dominos.com/olo/faces/login/login.jsp"
#ADD_COUPON_URL = "https://www01.order.dominos.com/olo/faces/order/coupons.jsp"
#BUILD_PIZZA_URL = "https://www01.order.dominos.com/olo/faces/order/step2_choose_pizza.jsp"
#ADD_PIZZA_URL = "https://www01.order.dominos.com/olo/faces/order/step2_build_pizza.jsp"
#CALCULATE_TOTAL_URL = "https://www01.order.dominos.com/olo/servlet/ajax_servlet"
#CALCULATE_TOTAL_URL_POST_VARS = {
#    "cmd": "priceOrder",
#    "formName": "orderSummaryForm:",
#    "getFreeDeliveryOffer": "N",
#    "runCouponPicker": "N",
#    "runPriceOrder": "Y",
#}
#ADD_SIDES_URL = ADD_PIZZA_URL
#CHECKOUT_URL = "https://www01.order.dominos.com/olo/faces/order/step3_choose_drinks.jsp"
#SUBMIT_ORDER_URL = "https://www01.order.dominos.com/olo/faces/order/placeOrder.jsp"
#LOGOUT_URL = "http://www01.order.dominos.com/olo/servlet/init_servlet?target=logout"


# Set User Agent
__version__ = "0.2.2"
USER_AGENT = {'User-agent' : 'PizzaPyParty/%s' % __version__}

# TODO (ryochan7): Organize toppings data strutures in a better manner
# Lists with default pizza attributes. Used when parsing pizza options passed
sizes = ("small", "medium", "large", "x-large")
crusts = ("handtoss", "deepdish", "thin", "brooklyn")
TOPPING_CHEESE, TOPPPING_SAUCE = ("toppingC", "toppingX")
#TOPPING_CHEESE, TOPPPING_SAUCE = ("topping-#-C-#-", "topping-#-X-#-")

###################################
####                           ####
####     Topping info          ####
####                           ####
###################################

#topping(code): code will specify if a topping is selected
#toppingSide(code): W - Whole Pizza
#                   1 - Left Side Only
#                   2 - Right Side Only
#                   Program will only allow on whole pizza
#toppingAmount(code):  1 - Normal
#                     .5 - Light
#                    1.5 - Extra
#                    Program only allow normal amount of topping


#### CHEESE & SAUCE ####
#toppingCHEESE:  Cheese (Irrelevant. Use toppingC)
#toppingC: toppingSideC: toppingAmountC: Cheese
#### Side seems irrelevant when it comes to sauce
#toppingSAUCE: toppingAmountSAUCE: Sauce (Irrelevant. Use specific sauce topping. Default: toppingX)
#toppingX: toppingSideX: toppingAmountX: New Robust Tomato Sauce
#toppingXw: toppingSideXw: toppingAmountXw: White Sauce
#toppingXm: toppingSideXm: toppingAmountXm: Hearty Marinara Sauce
#toppingBq: toppingSideBq: toppingAmountBq: BBQ Sauce

#### MEATS ####
#toppingP: toppingSideP: toppingAmountP: Pepperoni:
#toppingPl: toppingSidePl: toppingAmountPl: Extra Large Pepperoni
#toppingSb: toppingSideSb: toppingAmountSb: Sliced Italian Sausage
#toppingS: toppingSideS: toppingAmountS: Italian Sausage
#toppingB: toppingSideB: toppingAmountB: Beef
#toppingH: toppingSideH: toppingAmountH: Ham
#toppingK: toppingSideK: toppingAmountK: Bacon
#toppingDu: toppingSideDu: toppingAmountDu: Premium Chicken
#toppingSa: toppingSideSa: toppingAmountSa: Salami
#toppingPm: toppingSidePm: toppingAmountPm: Philly Steak

#### UNMEATS ####
#toppingG: toppingSideG: toppingAmountG: Green Peppers
#toppingR: toppingSideR: toppingAmountR: Black Olives
#toppingN: toppingSideN: toppingAmountN: Pineapple
#toppingM: toppingSideM: toppingAmountM: Mushrooms
#toppingO: toppingSideO: toppingAmountO: Onions
#toppingJ: toppingSideJ: toppingAmountJ: Jalapeno Peppers
#toppingZ: toppingSideZ: toppingAmountZ: Banana Peppers
#toppingSi: toppingSideSi: toppingAmountSi: Spinach
#toppingRr: toppingSideRr: toppingAmountRr: Roasted Red Peppers
#toppingE: toppingSideE: toppingAmountE: Cheddar Cheese
#toppingCp: toppingSideCp: toppingAmountCp: Shredded Provolone Cheese
#toppingCs: toppingSideCs: toppingAmountCs: Shredded Parmesan
#toppingFe: toppingSideFe: toppingAmountFe: Feta Cheese
#toppingV: toppingSideV: toppingAmountV: Green Olives
#toppingTd: toppingSideTd: toppingAmountTd: Diced Tomatoes
#toppingHt: toppingSideHt: toppingAmountHt: Hot Sauce


class Topping (object):

    """Holds information about different toppings.

    This class uses reference equality, so these objects should not be copied
    or reconstructed.
    """

    def __init__ (self, short_name, long_name, cryptic_code, help_name):
        self.short_name = short_name
        self.long_name = long_name
        self.cryptic_code = cryptic_code
        self.cryptic_name = "topping" + cryptic_code
        self.cryptic_num = "toppingSide" + cryptic_code
        self.help_name = help_name
        # This is the destination of the topping option.
        self.option_dest = self.long_name.replace('-', '_')


TOPPINGS = [
    Topping ("p", "pepperoni",        "P",  "Pepperoni"),
    Topping ("x", "xlarge-pepperoni", "Pl", "Extra Large Pepperoni"),
    Topping ("i", "italian-sausage",  "S",  "Italian Sausage"),
    Topping ("b", "beef",             "B",  "Beef"),
    Topping ("h", "ham",              "H",  "Ham"),
    Topping ("c", "bacon",            "K",  "Bacon"),
    Topping ("k", "chicken",          "Du", "Chicken"),
    Topping ("s", "philly-steak",     "Pm", "Philly Steak"),
    Topping ("g", "green-peppers",    "G",  "Green Peppers"),
    Topping ("l", "black-olives",     "R",  "Black Olives"),
    Topping ("a", "pineapple",        "N",  "Pineapple"),
    Topping ("m", "mushrooms",        "M",  "Mushrooms"),
    Topping ("o", "onions",           "O",  "Onions"),
    Topping ("j", "jalapeno-peppers", "J",  "Jalapeno Peppers"),
    Topping ("e", "banana-peppers",   "Z",  "Bananan Peppers"),
    Topping ("d", "cheddar-cheese",   "E",  "Cheddar Cheese"),
    Topping ("n", "provolone-cheese", "Cp", "Provolone Cheese"),
    Topping ("v", "green-olives",     "V",  "Green Olives"),
    Topping ("t", "tomatoes",         "Td", "Diced Tomatoes"),
]


# Old-style ad-hoc topping data structures.
toppings_long = [t.long_name for t in TOPPINGS]
short2topping = dict([(t.short_name, t) for t in TOPPINGS])
long2topping = dict([(t.long_name, t) for t in TOPPINGS])

help_text = (
    "            With Pepperoni",   "     With Extra Large Pepperoni",
    "      With Italian Sausage",   "                 With Beef",
    "                  With Ham",   "                With Bacon",
    "              With Chicken",   "         With Philly Steak",

    "        With Green Peppers",   "         With Black Olives",
    "            With Pineapple",   "            With Mushrooms",
    "               With Onions",   "     With Jalapeno Peppers",
    "       With Bananan Peppers",
    "       With Cheddar Cheese",     "     With Provolone Cheese",
    "         With Green Olives", "             With Diced Tomatoes",)

# Hack to associate the aligned help text with the topping.
for i, topping in enumerate (TOPPINGS):
    topping.help_text = help_text[i]


del help_text

# Dictionary used for pizza
default_pizza = {}.fromkeys (toppings_long, ['N', '1'])
default_pizza.update ({'crust': 'HANDTOSS'})
default_pizza.update ({'size': '10'})
default_pizza.update ({'quantity': '1'})
default_pizza.update ({'cheese': ['W', '1']})
default_pizza.update ({'sauce': ['W', '1']})


# Set the minimum and maximum amount of pizzas that can be ordered
MIN_QTY = 1
MAX_QTY = 25
MAX_TOTAL_QTY = 25
ORDERED_PIZZAS = 0


###########################################################
#                                                         #
#       Main Pizza Class and Page Parsing Classes         #
#                                                         #
###########################################################


#TODO: ABSTRACT AND SPLIT CLASS, FIX RIGID LOGIC
class Pizza (object):

    def __init__ (self):
        self.crust = ""
        self.size = ""
        self.quantity = ""
        self.toppings = set()
        self.order = default_pizza.copy ()


    ###########################################################
    #                                                         #
    #           Pizza Attributes Parsing Functions            #
    #                                                         #
    ###########################################################

    def addTopping (self, topping):
        """ Add a topping to a pizza """
        if not isinstance(topping, Topping):
            if topping in short2topping:
                topping = short2topping[topping]
            elif topping in long2topping:
                topping = long2topping[topping]
            else:
                print >> sys.stderr, "'%s' is not a valid topping choice. Exiting." % topping
                sys.exit (42)
        self.order[topping.long_name] = ['W', '1']
        self.toppings.add (topping)


    def setQuantity (self, quantity):
        """ Sets the quantity of the pizza based on the quantity passed """
        if self.quantity:
            print >> sys.stderr, """You cannot set the quantity for the same pizza twice.
Please check your command-line parameters. Exiting."""
            sys.exit (42)
        try:
            quantity = int (quantity)
        except ValueError:
            print >> sys.stderr, "The input value for quantity must be an integer. Exiting."
            sys.exit (42)
        if quantity >= MIN_QTY and quantity <= MAX_QTY:
            global ORDERED_PIZZAS
            if (quantity + ORDERED_PIZZAS <= MAX_TOTAL_QTY):
                self.order.update ({'quantity': str (quantity)})
                self.quantity = quantity
                ORDERED_PIZZAS += quantity
            else:
                print >> sys.stderr, "You cannot order more than %i pizzas. Exiting." % MAX_TOTAL_QTY
                sys.exit (42)
        else:
            print >> sys.stderr, "Bad value for quantity. Quantity must be between %i and %i. Exiting." % (MIN_QTY, MAX_QTY)
            sys.exit (42)


    def setSize (self, size):
        """ Sets the size of the piza based on the size choice passed """
        if self.size:
            print >> sys.stderr, """You cannot set the size twice. Please check your command
line parameters. Exiting."""
            sys.exit (42)
        if size == 'small':
            # Deepdish pizzas cannot be small size.
            # Will revert to medium size
            if self.crust == 'deepdish':
                print "Small size is not available for deepdish pizzas. Changing to medium."
                self.order.update ({'size': '12'})
                self.size = 'medium'
            elif self.crust == 'brooklyn':
                print "Small size is not available for brooklyn pizzas. Changing to large."
                self.order.update ({'size': '14'})
                self.size = 'large'
            else:
                self.order.update ({'size': '10'})
                self.size = size
        elif size == 'medium':
            if self.crust == 'brooklyn':
                print "Medium size is not available for brooklyn pizzas. Changing to large."
                self.order.update ({'size': '14'})
                self.size = 'large'
            else:
                self.order.update ({'size': '12'})
                self.size = size
        elif size == 'large':
            self.order.update ({'size': '14'})
            self.size = size
        elif size == 'x-large':
            # Deepdish and thin pizzas cannot be extra large size.
            # Will revert to large size
            if self.crust == 'deepdish':
                print "Extra large size is not available for deepdish pizzas. Changing to large."
                self.order.update ({'size': '14'})
                self.size = 'large'
            elif self.crust == 'thin':
                print "Extra large size is not available for thin pizzas. Changing to large."
                self.order.update ({'size': '14'})
                self.size = 'large'
            else:
                self.order.update ({'size': '16'})
                self.size = size
        else:
            print >> sys.stderr, "'%s' is not a valid size choice. Exiting." % size
            sys.exit (42)

    def setCrust (self, crust):
        """ Sets the crust of the pizza based on the curst choice passed """
        if self.crust:
            print >> sys.stderr, """You cannot set the crust twice. Please check your
command line parameters. Exiting."""
            sys.exit (42)
        if crust == 'handtoss':
            self.order.update ({'crust': 'HANDTOSS'})
            self.crust = crust
        # Deepdish pizzas can only be of medium or large sizes
        elif crust == 'deepdish':
            if self.size == 'small':
                print "Small size is not available for deepdish pizzas. Changing to medium."
                self.order.update ({'size': '12'})
                self.size = 'medium'
            elif self.size == 'x-large':
                print "Extra large size is not available for deepdish pizzas. Changing to large."
                self.order.update ({'size': '14'})
                self.size = 'large'
            self.order.update ({'crust': 'DEEPDISH'})
            self.crust = crust
        elif crust == 'thin':
            # Thin pizzas cannot be extra large size
            if self.size == 'x-large':
                print "Extra large size is not available for thin pizzas. Changing to large."
                self.order.update ({'size': '14'})
                self.size = 'large'
            self.order.update ({'crust': 'THIN'})
            self.crust = crust
        elif crust == 'brooklyn':
            if self.size == 'small' or self.size == 'medium':
                print "The smallest available size for brooklyn pizzas is large. Changing to large."
                self.order.update ({'size': '14'})
                self.size = 'large'
            self.order.update ({'crust': 'BK'})
            self.crust = crust
        else:
            print >> sys.stderr, "'%s' is not a valid crust choice. Exiting."
            sys.exit (42)


class BasicFormData (object):
    def __init__ (self):
        self.form_data = {}
        self.form_action = None


class CouponCodeData (object):
    def __init__ (self):
        self.form_data = []
        self.form_action = None


class ParseCoupons (htmllib.HTMLParser):
    """ Parser for the coupons page. Obtains all available coupon offers """
    def __init__(self):
        f = formatter.NullFormatter ()
        htmllib.HTMLParser.__init__ (self)
        self.in_coupon_menu = False
        self.in_ul = False
        self.getcoupon = False
        self.id = ""
        self.description = ""
        self.price = -1.0 # Arbitrary non-blank default value
        self.type = ""
        self.form = CouponCodeData ()
        self.pattern = re.compile (r".*document\.forms\['couponsForm'\]\['couponCode'\]\.value='((?:_)?\d{4})'")


    def start_form (self, attrs):
        getaction = False
        for item, value in attrs:
            if item == "id" and value == "couponsForm":
                getaction = True
            elif item == "action" and getaction:
                self.form.form_action = value

    def start_div (self, attrs):
        for item, value in attrs:
            # Get scope for full coupon listing. Helps avoid duplicates
            if item == "class" and value == "menutype seeall":
                self.in_coupon_menu = True
            elif item == "class" and value == "coupon-price" and self.in_coupon_menu:
                self.save_bgn ()
                self.type = "coupon-price"


    def end_div (self):
        # If working outside of main coupon display, ignore
        if not self.in_coupon_menu:
            return

        # Get price from text buffer
        if self.type == "coupon-price":
            text = self.save_end ()
            self.price = text.decode ("utf8", "ignore")
            self.type = ""

    def start_ul (self, attrs):
        # If working outside of main coupon display, ignore
        if not self.in_coupon_menu:
            return

        # Note beginning of coupon list
        self.in_ul = True

    def end_ul (self):
        if self.in_ul:
            # At end of coupon list
            self.in_coupon_menu = False
            self.in_ul = False


    def start_li (self, attrs):
        # If working outside of main coupon display, ignore
        if not self.in_coupon_menu or not self.in_ul:
            return

        for item, value in attrs:
            if item == "class" and value == "coupon-item" or value == "coupon-item first-item":
                self.getcoupon = True # Only set True when in "menutype seeall" div scope


    def end_li (self):
        if self.getcoupon:
            # End of coupon entry
            self.getcoupon = False


    def start_a (self, attrs):
        # If working outside of list item, ignore
        if not self.getcoupon:
            return

        for item, value in attrs:
            if item == 'onclick':
                match = self.pattern.search (value)
                if not match:
                    raise Exception ("Necessary item 'couponCode' was not found on the page")
                temp = match.group (1)
                self.id = temp
            elif item == "title":
                self.description = value


    # Append item and information to form data
    def end_a (self):
        # If working outside of list item, ignore
        if not self.getcoupon:
            return

        if self.id and self.description and self.price != -1.0:
            self.form.form_data.append ((self.id, self.description, self.price))
        self.id = ""
        self.description = ""
        self.price = -1.0 # Arbitrary non-blank default value
        self.type = ""


class Parser (htmllib.HTMLParser):
    """ Generic parser used to parse the pages and obtain the form data """
    def __init__(self, form_id, verbose=False):
        f = formatter.NullFormatter ()
        htmllib.HTMLParser.__init__ (self)
        self.form_id = form_id
        self.getform = False
        self.select_name = None
        self.option_value = None
        self.first_option_value = None
#        self.formdata = {}
        self.form = BasicFormData ()
        self.formdata = self.form.form_data



    def do_form (self, attrs):
        for item, value in attrs:
            if item == "id" and value == self.form_id:
                self.getform = True
                #return
            elif item == "action":
                self.form.form_action = value

        if self.getform and self.form.form_action:
            return

        self.getform = False


    def do_input (self, attrs):
        # If working outside of desired form, ignore
        if not self.getform:
            return

        name = tmp_value = None
        radio_field = checked = False
        for item, value in attrs:
            if item == "name":
                name = value
            elif item == "value":
                tmp_value = value
            if item == "type" and value == "radio":
                radio_field = True
            elif item == "checked":
                checked = True

        if name and tmp_value != None:
            # Check if a radio field needs to be updated
            if radio_field and checked:
                self.formdata.update ({name: tmp_value})
            # Update non-radio fields
            elif not radio_field:
                self.formdata.update ({name: tmp_value})
        # Include any input with no specified value
        # (in some needed hidden fields). Ex. login:_idcl
        elif name:
            self.formdata.update ({name: ""})


    def start_select (self, attrs):
        # If working outside of desired form, ignore
        if not self.getform:
            return

        for item, value in attrs:
            if item == "name":
                self.select_name = value


    def do_option (self, attrs):
        # If working outside of desired form, ignore
        if not self.getform:
            return

        attrs = dict(attrs)
        value = attrs.get("value", None)
        if "selected" in attrs:
            if value is None:
                raise Exception("TODO: Support options w/o value attrs")
            self.option_value = value

        if not self.first_option_value:
            self.first_option_value = value
        #self.last_option_value = value


    def end_select (self):
        # If working outside of desired form, ignore
        if not self.getform:
            return

        # If no option is selected (should not happen),
        # make first grabbed value the selected value
        if not self.option_value:
            self.option_value = self.first_option_value
#            self.option_value = self.last_option_value

        if self.select_name and self.option_value:
            self.formdata.update ({self.select_name: self.option_value})

        # Reset these.
        self.select_name = None
        self.option_value = None
        self.first_option_value = None
#        self.last_option_value = None


###########################################################
#                                                         #
#                   Helper Functions                      #
#                                                         #
###########################################################

def pretty_print(d):
    """Pretty print a dictionary."""
    return "{\n%s\n}" % "\n".join("    %r: %r," % (k, v)
                                  for k, v in sorted(d.items()))

def getPage (url, data=None):
    """ Generic function that makes requests for pages """
    if data != None:
        data = urlencode (data)
    try:
        req = urllib2.Request (url, data, USER_AGENT)
        handle = urllib2.urlopen (req)
    except:
        raise Exception ("Could not get page %s." % url)

    page = handle.read ()
    handle.close ()
    return page

def getFormData (scan_page, target_form):
    """ Calls the main Parser class to obtain the form data of a page """
    parsed_form = Parser (target_form)
    #try:
    parsed_form.feed (scan_page)
    #except Exception:
    #    dumpPage (scan_page)
    parsed_form.close ()
#    print parsed_form.formdata
    return parsed_form.form


def setFormField (current_data, name, new_value):
    """ Check that a particular entry exists in the form data
        and updates the entry with the value passed """
    if not name in current_data:
        raise Exception ("Necessary item \"%s\" was not found in the form.\n"
                         "Current form data: %s" %
                         (name, pretty_print(current_data)))

    current_data.update ({name: new_value})

def mergeAttributes (parsed_conf, username, password, pizza):
    """ Merge attributes specified in the config file and any attributes
        specified on the command line """
    if not username:
        username = parsed_conf["username"]
    if not password:
        password = parsed_conf["password"]
    if not pizza.crust:
        pizza.setCrust(parsed_conf["default_crust"])
    if not pizza.size:
        pizza.setSize (parsed_conf["default_size"])
    if not pizza.quantity:
        pizza.setQuantity (parsed_conf["default_quantity"])
    if not pizza.toppings:
        for new_topping in parsed_conf["default_toppings"]:
            pizza.addTopping (new_topping)
    return username, password

def findMissingAttributes (data_list):
    """ Find the first attribute that is blank, print what the missing
        attribute is, and then exit """
    index = data_list.index ('')

    failed_value = ''
    if index == 0:
        failed_value = 'username'
    elif index == 1:
        failed_value = 'password'
    elif index == 2:
        failed_value = 'crust'
    elif index == 3:
        failed_value = 'size'
    elif index == 4:
        failed_value = 'quantity'
    print >> sys.stderr, "A value for '%s' was not specified. Exiting." % failed_value
    sys.exit (42)

def checkLogin (scan_page):
    """ Check whether the login was successful. Quits the program if the login
        was not successful """
    pattern = re.compile ("Incorrect User Name/Password.")
    match = pattern.search (scan_page)
    if match:
        print >> sys.stderr, "Incorrect User Name/Password. Exiting."
        sys.exit (42)
    return True

def storeClosed (scan_page):
    """ Checks to see if the local Domino's store is closed.
        Quits the program if it is closed """
    pattern = re.compile ('Store Currently Closed')
    match = pattern.search (scan_page)
    if match:
        print "Your local Domino's store is currently closed. Exiting."
        sys.exit (42)
    return False

def dumpPage (page):
    with open('dumped_page.html', 'w') as page_out:
        page_out.write(page)


#####################################################################
#                                                                   #
#    Main Function Flow (Gets Pages, Add Items, Output, Read Conf)  #
#                                                                   #
#####################################################################


def getLoginPage ():
    """ Only needed to get the necessary cookie data """
    print "Getting login page..."
    newpage = getPage (LOGIN_URL)
    return newpage

def getLoginInfo ():
    """ Take input for the username and password needed to login to the Domino's site """
    print "Enter your username:",
    username = raw_input ()
    password = getpass ("Enter your password: ")
    return [username, password]

def Login (current_page, username, password):
    """ Login to the Domino's site """
    form = getFormData (current_page, "login")
    formdata = form.form_data

    setFormField (formdata, 'login:usrName', username)
    setFormField (formdata, 'login:passwd', password)
    setFormField (formdata, 'login:_idcl', 'login:submitLink')

    print "Logging in as %s..." % username

    #next_url = urllib2.urlparse.urljoin (TEST_ROOT, form.form_action)
    #newpage = getPage (next_url, formdata)
    newpage = getPage (LOGIN_URL, formdata)
    checkLogin (newpage)
    return newpage

def startBuildPizza (current_page):
    """ Gets the page that holds the main form for specifying a pizza """
    form = getFormData (current_page, "choose_pizza")
    formdata = form.form_data

    setFormField (formdata, 'choose_pizza:_idcl', 'choose_pizza:goToBuildOwn')
    #next_url = urllib2.urlparse.urljoin (TEST_ROOT, form.form_action)
    #print next_url
    #newpage = getPage (next_url, formdata)
    newpage = getPage (BUILD_PIZZA_URL, formdata)
    #dumpPage (newpage)
    return newpage

def addPizza (current_page, pizza, check_coupon=''):
    """ Add the user's custom pizza onto the order """
    form = getFormData (current_page, "build_own")
    formdata = form.form_data

    # Delete any unknown toppings
    formdata_temp = formdata.copy ()
    topping_re = re.compile (r"topping(?!Side|Amount).*")
    temp_topping_keys = [t.cryptic_name for t in TOPPINGS]
    for key, value in formdata_temp.iteritems ():
        # If key is cheese or sauce, skip
        if key == TOPPING_CHEESE or key == TOPPPING_SAUCE:
            continue
        elif topping_re.match (key) and key not in temp_topping_keys:
            del formdata[key]
    del formdata_temp

    for topping in TOPPINGS:
        if topping in pizza.toppings:
            # Fill field with topping settings.
            setFormField (formdata, topping.cryptic_num,
                          pizza.order[topping.long_name][0])
        else:
            # Unused toppings must be removed from form data
            topping_field = topping.cryptic_name
            if topping_field in formdata:
                del formdata[topping_field]

    setFormField (formdata, "builderCrust", pizza.order["crust"])
    setFormField (formdata, "builderSize", pizza.order["size"])
    setFormField (formdata, "builderQuantity", pizza.order["quantity"])
    setFormField (formdata, "build_own:_idcl", "build_own:doAdd")
    #print formdata

    newpage = getPage (ADD_PIZZA_URL, formdata)
    #next_url = urllib2.urlparse.urljoin (TEST_ROOT, form.form_action)
    #print next_url
    #newpage = getPage (next_url, formdata)
    #dumpPage (newpage)
    return newpage

def calculateTotal ():
    """ Gets the total for an order. Needed to run prior to
        going to the confirmation page or the total cannot be obtained
        due to the use of AJAX """
    newpage = getPage (CALCULATE_TOTAL_URL, CALCULATE_TOTAL_URL_POST_VARS)
    #dumpPage (newpage)
    a = dom.parseString (newpage)
    order_total = a.getElementsByTagName ('total')[0].firstChild.data
    return order_total

def getSidesPage (current_page, check_coupon=''):
    """ Gets the sides page """
    form = getFormData (current_page, "build_own")
    formdata = form.form_data

    setFormField (formdata, 'build_own:_idcl', 'build_own:navSidesLink')
#    print formdata

    newpage = getPage (ADD_SIDES_URL, formdata)
    #next_url = urllib2.urlparse.urljoin (TEST_ROOT, form.form_action)
    #print next_url
    #newpage = getPage (next_url, formdata)
    return newpage

def getConfirmationPage (current_page):
    """ Gets the confirmation page """
    form = getFormData (current_page, "orderSummaryForm")
    formdata = form.form_data

    setFormField (formdata, 'orderSummaryForm:_idcl', 'orderSummaryForm:osCheckout')
    #next_url = urllib2.urlparse.urljoin (TEST_ROOT, form.form_action)
    #print next_url
    #newpage = getPage (next_url, formdata)
    newpage = getPage (CHECKOUT_URL, formdata)
    #dumpPage (newpage)
    return newpage

def submitFinalOrder (current_page, total, check_force):
    """ Submits the final order to Domino's """
    choice = ""
    if not check_force:
        print "Confirmation: order for %s (y|yes|n|no)?" % (total),
        choice = raw_input ()
    if check_force or choice.lower () == 'y' or choice.lower () == 'yes':
        form= getFormData (current_page, "pricingEnabled")
        formdata = form.form_data
        setFormField (formdata, 'pricingEnabled:_idcl', 'pricingEnabled:placeOrdeLinkHIDDEN')

        print "Checking out for your order of %s..." % total
        # Sends the final order data to Domino's. After this point,
        # the order is complete. Comment the getPage line below if you want
        # to test the entire program, including this function,
        # without submitting the final order
        newpage = getPage (SUBMIT_ORDER_URL, formdata)
        return True
    elif choice.lower () == 'n' or choice.lower () == 'no':
        return False
    else:
        raise Exception ("You made an invalid choice.")

def Logout ():
    """ Logs the user off of the site """
    print "Logging out..."
    page = getPage (LOGOUT_URL)

def outputOrder (pizza):
    """ Outputs the current order in a readable format """
    print "%s %s, %s" % (pizza.quantity, pizza.size, pizza.crust),

    length = len (pizza.toppings)

    if pizza.quantity > 1 and length > 0:
        print "pizzas with",
    elif pizza.quantity > 1:
        print "pizzas..."
    elif length > 0:
        print "pizza with",
    else:
        print "pizza..."

    for i, topping in enumerate (pizza.toppings):
        # Use space when printing topping name
        topping_name = topping.long_name.replace ('-', ' ')

        if length > 2 and (length - i) >= 2:
            print "%s," % topping_name,
        elif length == 1:
            print "%s..." % topping_name
        # Used to print first of two toppings
        elif (length - i) == 2:
            print "%s" % topping_name,
        else:
            print "and %s..." % topping_name


VERSION_STR = "Pizza Py Party %s" % __version__

USAGE = """\
%%prog [OPTIONS] [TOPPINGS] [QUANTITY] [SIZE] [CRUST]

%(VERSION_STR)s

QUANTITY can be between %(MIN_QTY)s and %(MAX_QTY)s.
No more than %(MAX_TOTAL_QTY)s pizzas can be ordered.

SIZE can be: small, medium, large, or x-large.
Note: small is not available for deepdish or brooklyn.
      medium is not available for brooklyn
      x-large is not available for deepdish, thin.

CRUST can be: handtoss, deepdish, thin, or brooklyn.

Example: `pizza-py-party -pmd 2 medium thin` orders 2 medium, thin pizzas with
pepperoni, mushrooms, and cheddar cheese.

See the man page for more details on accounts, configuration files, and batch
ordering.
""" % globals()


def parseArguments (command_list, cur_pizza, skip_flags=False):
    formatter = optparse.IndentedHelpFormatter (max_help_position=30)
    parser = optparse.OptionParser (usage=USAGE, version=VERSION_STR,
                                    add_help_option=False, formatter=formatter)

    if not skip_flags:
        parser.add_option ("-U", "--username", help="Specify your user name")
        parser.add_option ("-P", "--password", help="Specify your password")
        parser.add_option ("-O", "--coupon", default="", help="Specify an "
                           "online coupon. Input x to see the coupon menu")
        parser.add_option ("-F", "--force", action="store_true",
                           help="Order the pizza with no user confirmation")
        parser.add_option ("-L", "--login", action="store_true",
                           help="Specify login information within the "
                           "program as opposed to using the command "
                           "line arguments")
        parser.add_option ("-I", "--input-file", help="Input file to read "
                           "batch of pizza (see man page for info)")
        parser.add_option ("-H", "--help", action="help",
                           help="Display help text")

    topping_opts = optparse.OptionGroup(parser, "Topping options")
    for topping in TOPPINGS:
        short = "-" + topping.short_name
        long = "--" + topping.long_name
        topping_opts.add_option (short, long, dest=topping.option_dest,
                                 action="store_true", help=topping.help_name)
    parser.add_option_group(topping_opts)

    (options, args) = parser.parse_args(command_list)

    # For each topping, check if the option was set.  If so, add it to the
    # pizza.
    for topping in TOPPINGS:
        if getattr(options, topping.option_dest):
            cur_pizza.addTopping(topping)

    # Parse positional arguments
    for argument in args:
        if argument in sizes:
            cur_pizza.setSize (argument)
        elif argument in crusts:
            cur_pizza.setCrust (argument)
        elif argument.isdigit ():
            cur_pizza.setQuantity (argument)
        else:
            print >> sys.stderr, "'%s' is not a valid argument. Exiting." % argument
            sys.exit (42)

    return [options.username, options.password, options.coupon, options.force,
            options.login, options.input_file]


def getCouponsPage (current_page):
    """ Gets the coupon page """
    form = getFormData (current_page, "choose_pizza")
    formdata = form.form_data

    setFormField (formdata, 'choose_pizza:_idcl', 'choose_pizza:couponsButton')
    # Needed for me since no Domino's store delivers to me
    #setFormField (formdata, 'startOrder:deliveryOrPickup', 'Pickup')

    #next_url = urllib2.urlparse.urljoin (TEST_ROOT, form.form_action)
    #newpage = getPage (next_url, formdata)
    newpage = getPage (ADD_COUPON_URL, formdata)
    storeClosed (newpage)
    return newpage

def getAvailableCoupons (current_page):
    """ Calls the ParseCoupons class to obtain the available coupon offers """
    parsed_page = ParseCoupons ()
    parsed_page.feed (current_page)
    parsed_page.close ()
    return parsed_page.form

def printAvailableCoupons (coupon_data):
    """ Print the available coupon offers """
    print
    print "Coupon Menu"
    print "----------------"
    print
    for id, desc, price in coupon_data:
        print "Coupon ID#: %s" % id
        print "Description: %s" % desc
        if not price:
            price = "Read description for details"
        print "Price: %s" % price
        print
    print
    print """Coupon offers are not validated within this program so make sure
to pick a proper order for the coupon you use. Also, coupon offers
are subject to change so be cautious if using this program
with a coupon offer under cron."""

def addCoupon (current_page, coupon, coupon_data):
    """ Add the coupon code to the user's order """
    form = getFormData (current_page, "couponsForm")
    formdata = form.form_data

    # Take the coupon_data list, place the coupon ids in a temporary list,
    # and find out if the coupon code specified is valid
    temp = []
    for id, desc, price in coupon_data:
        temp.append (id)
    if not coupon in temp:
        raise Exception ("'%s' is not a valid coupon code." % coupon)

    setFormField (formdata, 'couponCode', coupon)
    setFormField (formdata, 'couponsForm:_idcl', 'couponsForm:addCouponLink')

    newpage = getPage (ADD_COUPON_URL, formdata)
    #next_url = urllib2.urlparse.urljoin (TEST_ROOT, form.form_action)
    #newpage = getPage (next_url, formdata)
    return newpage

def filter_comments_and_blanks_and_strip (lines):
    """Filter comment lines and blanks from lines in a text file."""
    for line in lines:
        line = line.strip ()
        if line.startswith ('#'):
            continue
        if not line:
            continue
        yield line

def readConfFile ():
    """ Parse the configuration file, if it exists,
        and return the values obtained """
    home = os.path.expanduser ("~")
    path = os.path.join (home, ".pizza-py-party.conf")
    if not os.path.isfile (path):
        return False

    defaults = dict.fromkeys (["username", "password", "default_quantity",
                               "default_size", "default_crust",
                               "default_toppings"], "")

    with open (path, 'r') as conf_file:
        for line in filter_comments_and_blanks_and_strip (conf_file):
            parts = line.split('=', 2)
            if len (parts) == 2 and parts[0] in defaults:
                (key, value) = parts
                defaults[key] = value
            else:
                print >> sys.stderr, ("Invalid line has been detected.\n"
                                      "\"%s\"\nExiting.") % line.strip()
                sys.exit (42)

    # Toppings should be a space-separated list.  Make it a Pythonn list.
    defaults["default_toppings"] = defaults["default_toppings"].split ()

    return defaults

def parseBatchFile (batchfile):
    """ Parse the specified batch file and return a list of the lines read """
    if not os.path.isfile (batchfile):
        print "The input file does not exist. Exiting."
        sys.exit (42)
    with open (batchfile, 'r') as file:
        return [l.split() for l in strip_and_filter_comments_and_blanks (file)]


###########################################################
#                                                         #
#                    Primary Program                      #
#                                                         #
###########################################################


def main (argv):
    # Assign default lists and a default Pizza object
    pizza_list = []
    pizza_commands = []
    pizza = Pizza ()

    # Parse command-line arguments
    username, password, coupon, force, login, input_file = \
            parseArguments (argv[1:], pizza)

    # If a pizza was defined in the command-line arguments, add it to the pizza
    # list. Else, delete the initial Pizza object
    if pizza.crust or pizza.size or pizza.quantity or pizza.toppings:
        pizza_list.append (pizza)
    else:
        del pizza

    # If a batch file was specified on the command-line,
    # parse it and store the result in a list
    if input_file:
        pizza_commands = parseBatchFile (input_file)

    # Parse the arguments found in the batch file and add any
    # pizzas to the pizza list. Will be skipped if no batch
    # file was specified
    for arguments in pizza_commands:
        pizza = Pizza ()
        parseArguments (arguments, pizza, True)
        pizza_list.append (pizza)

    # Only allow interactive login if no value has been
    # specified for the username or password
    if not username and not password and login:
        username, password = getLoginInfo ()
        print

    # Parse the config file if one exists
    parsed_conf = readConfFile ()
    if parsed_conf:
        # If a pizza has not been defined and a config file was parsed,
        # add a blank Pizza object to the list and check for any default values
        if len (pizza_list) == 0:
            pizza = Pizza ()
            pizza_list.append (pizza)
        # Merge the default config attributes with the pizzas in the list
        for pizza in pizza_list:
            username, password = mergeAttributes (parsed_conf, username, password, pizza)

    # If no pizzas have been specified in any way and the user is
    # not going to see the coupon menu,
    # tell the user about the problem and exit the program
    if len (pizza_list) == 0 and not coupon.lower() == 'x':
        print "You have not selected any pizzas. Exiting."
        sys.exit (42)

    # Check that the username and password have been specified
    # if the user wants to check out the coupon menu
    if coupon.lower() == 'x':
        if not username or not password:
            temp_list = [username, password]
            findMissingAttributes (temp_list)
    else:
        # If a necessary variable has not been defined, find the first undefined
        # variable and exit the program
        for pizza in pizza_list:
            if (not username or not password or not pizza.crust or
                not pizza.size or not pizza.quantity):
                temp_list = [username, password, pizza.crust, pizza.size, pizza.quantity]
                findMissingAttributes (temp_list)

    # Output the user order in a readable form. Skip this section
    # if the user wants to see the coupon menu
    if not coupon.lower() == 'x':
        print "Order: ",
        i = 0
        for pizza in pizza_list:
            if i > 0:
                print "       ",
            outputOrder (pizza)
            i += 1
        print

    # Get login page (required to get primary cookie)
    page = getLoginPage ()

    # Go to Step 1 section (Account Page)
    page = Login (page, username, password)
    username = ""
    password = ""

    if coupon and coupon.lower() == 'x':
        # Get coupons page, print the available coupons, and exit
        page = getCouponsPage (page)
        coupon_form = getAvailableCoupons (page)
        coupon_data = coupon_form.form_data
        printAvailableCoupons (coupon_data)
        sys.exit ()
    elif coupon:
        # Get coupons page, parse available coupons,
        # and add the coupon if the coupon code exists
        page = getCouponsPage (page)
        coupon_form = getAvailableCoupons (page)
        coupon_data = coupon_form.form_data
        page = addCoupon (page, coupon, coupon_data)
    else:
        # Go to Step 2 section and get pizza form
        page = startBuildPizza (page)

    # Add the specified pizza to the order
    for pizza in pizza_list:
        page = addPizza (page, pizza, coupon)

    # Go to Step 3 section (Choose Sides/Drinks section)
    page = getSidesPage (page, coupon)

    # Calculate order total
    order_total = calculateTotal ()

    # Go to Step 4 section (Confirm Order section)
    page = getConfirmationPage (page)

    # Show the order for the final confirmation
    pizza_list_length = len (pizza_list)
    if pizza_list_length == 1:
        print "Submitting order for",
    else:
        print "Submitting order for:"
    for pizza in pizza_list:
        if pizza_list_length != 1:
                print "  ",
        outputOrder (pizza)

    # Prompt the user to confirm the order. Exit the program
    # if the user chooses no
    if not submitFinalOrder (page, order_total, force):
        print "Exiting."
        sys.exit ()

    # Logout and go to the home page
    Logout ()

    print
    print "You should receive a copy of your receipt in your email shortly."


if __name__ == "__main__":
    main (sys.argv)
