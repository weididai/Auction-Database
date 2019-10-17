#!/usr/bin/env python
from operator import itemgetter
import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!


import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################

# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

urls = ('/currtime', 'curr_time',
        '/selecttime', 'select_time',
        # TODO: add additional URLs here
        '/search', 'search',
        '/add_bid','add_bid',
        '/search_result', 'search_result',

        # first parameter => URL, second parameter => class name
        )



class add_bid:
    def GET(self):
        return render_template('add_bid.html', message = "Please enter a bid!")
    def POST(self):
        post_params = web.input()
        itemID = post_params['itemID']
        userID = post_params['userID']
        amount = post_params['price']
        # insert a bid
        # 1. trigger4 will increase the number of bids for that item
        # 2. trigger3 checks new amount is higher that previous amount
        # 3. trigger5,6 check this bid's time cannot outside start and end time
        # 5. userID and itemID must exist gauranteed by foreigh key constraints
        # 6. trigger 8 set the current price to be the new amount
        # 7. we need to check that auction is closed if buy price is reached
        # TODO 4
        t = sqlitedb.transaction()
        try:
            #check if user enter all filelds
            if userID == "" or itemID == "" or amount == "":
                raise Exception("Please fill in all information!!")
            else:
                #check if this auction is open or not
                if not sqlitedb.checkStatus(itemID):
                    raise Exception("This auction is closed!")
                else:
                    sqlitedb.insertBids(itemID, userID, amount)
        except:
            t.rollback()
            print("error!!!")
            #print(str(e))
            return render_template('add_bid.html', message = "Invalid Input! Please try again to fill in corret data!")
        else:
            t.commit()
            return render_template('add_bid.html', message = "Your bid has been added!", add_result = "success")


class search:
    def GET(self):
        return render_template('search.html')

    def POST(self):
        post_params = web.input()
        itemID = post_params['itemID']
        userID = post_params['userID']
        category = post_params['category']
        itemDesc = post_params['itemDesc']
        minPrice = post_params['minPrice']
        maxPrice = post_params['maxPrice']
        status = post_params['status']
        t = sqlitedb.transaction()
        try:
            Items = sqlitedb.search(itemID, userID, category, itemDesc, maxPrice, minPrice, status)
            result = {}
            item_list = []
            category_list = []
            Bid_list = []
            winner_list = []
            for itemID in Items:
                item = sqlitedb.getItemById(itemID)
                item_list.append(item)
                category_list.append(sqlitedb.getCategoryByID(itemID))
                currTime = sqlitedb.getTime()
                #check if buy_price is reached
                if item.Buy_Price != None and item.Buy_Price <= item.Currently and item.Number_of_Bids != 0:
                    status = "Closed"
                else:
                    if currTime < item.Started:
                        status = 'NotStarted'
                    elif currTime > item.Ends:
                        status = 'Closed'
                    else:
                        status = 'Open'
                Bid_list.append(sqlitedb.getBidsByID(itemID))
                winner = None
                if status == 'Closed':
                    winner = sqlitedb.getWinnerByID(itemID)
                winner_list.append(winner)
                #print(map(itemgetter('Category'), sqlitedb.getCategoryByID(itemID)))
        except Exception as e:
            t.rollback()
            print(str(e))
            return render_template('search.html', message = str(e))
        else:
            t.commit()
            return render_template('search_result.html', Item = item_list, Categories = category_list, status = status, Bids = Bid_list, Winner = winner_list)


class curr_time:
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)



class select_time:
    # Aanother GET request, this time to the URL '/selecttime'
    def GET(self):
        return render_template('select_time.html')

    # A POST request
    #
    # You can fetch the parameters passed to the URL
    # by calling `web.input()' for **both** POST requests
    # and GET requests
    def POST(self):
        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss']
        enter_name = post_params['entername']

        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)
        update_message = '(Hello, %s. Previously selected time was: %s.)' % (enter_name, selected_time)
        # TODO: save the selected time as the current time in the database
        t = sqlitedb.transaction()
        try:
            sqlitedb.setTime(selected_time)
        except Exception as e:
            t.rollback()
            print str(e)
            return render_template('select_time.html', message = "Please selete the correct time!")
        else:
            t.commit()
            return render_template('select_time.html', message=update_message)
        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'


###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
