import json
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
from ranking_utils import Competitor, Match, RatingPeriod
from datetime import datetime
from pytz import timezone
import os
import sys


tz_pacific = timezone('US/Pacific')
tz_utc = timezone('UTC')

def length_to_letter(n):
    return chr(n + ord('A') - 1)

def sort_competitors(competitor_list):
    # list is sorted in ascending order. Insertion will reverse to descending order
    return sorted(competitor_list, key = lambda k: k.rating)
    
def wipe(sheet):
    records = sheet.get_all_records()
    if records:
        col_stop = length_to_letter(len(records[0]))
        row_stop = len(records) + 1
        cell_list = sheet.range('A2:{0}{1}'.format(col_stop, row_stop))
        for i, val in enumerate(cell_list):
            cell_list[i].value = ""
        sheet.update_cells(cell_list)

def move_ratings_data(current, archive):
    for item in current.get_all_records():
        archive.insert_row([item['Date'], item['Player1'], item['Player2'], item['Winner']], index = 2)

def gconnect_with_key(key_file):
    json_key = json.load(open(key_file))
    scope = scope = ['https://spreadsheets.google.com/feeds']
    credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), scope)
    return gspread.authorize(credentials)

def update_book(ss_name, connection):
    book = connection.open(ss_name)
    rp = RatingPeriod()
    competitors_sheet = book.worksheet("Ratings")
    competitors = competitors_sheet.get_all_records()
    competitors = [Competitor(name = c['Player'],
                                r = c['Rating'],
                                rd = c['RD'],
                                last_updated = tz_pacific.localize(
                                    datetime.strptime(c['Last-Played'], '%m/%d/%Y')
                                    )) 
                                for c in competitors]
    for c in competitors:
        rp.add_competitor(c)
    results_sheet = book.worksheet("Results")
    new_matches = results_sheet.get_all_records()
    for mtch in new_matches:
        p1 = mtch['Player1']
        p2 = mtch['Player2']
        w = mtch['Winner']
        p1 = rp.competitors[p1]['Competitor']
        p2 = rp.competitors[p2]['Competitor']
        w = rp.competitors[w]['Competitor']
        mtch_date = tz_pacific.localize(datetime.strptime(mtch['Date'], '%m/%d/%Y'))
        rp.add_match(Match(mtch_date, p1, p2, w))
    rp.make_new_rankings()
    wipe(competitors_sheet)
    print '\nwiped sheet\n'
    for c in sort_competitors([rp.competitors[k]['new_metrics'] for k in rp.competitors.keys()]):
        print c, '\n'
        competitors_sheet.insert_row([c.name, c.rating, c.RD, c.last_updated.strftime('%m/%d/%Y')], index = 2)
    print '\nupdated ratings\n'
    move_ratings_data(results_sheet, book.worksheet('Archived Results'))
    print '\nmoved match data\n'
    wipe(results_sheet)
    print 'wiped results'

def main(ss_names):
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'power-rankings-3152e30f4b4b.json')
    gc = gconnect_with_key(key_file)
    for ss_name in ss_names:
        update_book(ss_name, gc)

if __name__ == "__main__":
    print sys.argv[1:]
    main(sys.argv[1:])
    
#
#results = book.worksheet('Results')
#archived_results = book.worksheet('Archived Results') 
##results.insert_row(['11/10/2015', 'Alpha', 'Charlie', 'Alpha'], index = 10)
##print results.get_all_records()
#new_results = results.get_all_records()
#for result in new_results:
#    archived_results.insert_row([result['Date'], result['Player1'], result['Player2'], result['Winner']], index = 2)
#print results.row_count
#print len(new_results)
#
#
#cell_list = results.range('A2:D{0}'.format(len(new_results)+1))
#for i,val in enumerate(cell_list):
#    cell_list[i].value = ""
#results.update_cells(cell_list)
