import json
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
from ranking_utils import Competitor, Match, RatingPeriod

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


if __name__ == "__main__":
    json_key = json.load(open('/Users/alexegan1/Documents/python/power_ranking/power-rankings-3152e30f4b4b.json'))
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), scope)
    gc = gspread.authorize(credentials)
    book = gc.open('Power_Ranking')
    rp = RatingPeriod()
    competitors_sheet = book.worksheet("Ratings")
    competitors = competitors_sheet.get_all_records()
    competitors = [Competitor(name = c['Player'],
                                r = c['Rating'],
                                rd = c['RD'],
                                last_updated = c['Last-Played']) 
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
        rp.add_match(Match(mtch['Date'], p1, p2, w))
    rp.make_new_rankings()
    wipe(competitors_sheet)
    for c in sort_competitors([rp.competitors[k]['new_metrics'] for k in rp.competitors.keys()]):
        competitors_sheet.insert_row([c.name, c.rating, c.RD, c.last_updated], index = 2)
    
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
