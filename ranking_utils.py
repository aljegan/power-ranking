from math import log, sqrt, pi
from datetime import datetime
from pytz import timezone

DEFAULT_RATING = 1500
DEFAULT_RD = 350
q = log(10)/400
### rating periods are days, assume it take 2 years for informatio to decay entirely
c = sqrt((350**2 - 50**2)/float(730))

tz_pacific = timezone('US/Pacific')
tz_utc = timezone('UTC')

def g(RD):
    return float(1)/sqrt(1+3*(q**2)*(RD**2)/(pi**2))

def E_s(r, r_j, RD_j):
    exponent =-1*g(RD_j)*(r-r_j)/float(400)
    return float(1)/(1+10**exponent)

class Competitor(object):
    
    def __init__(self, name, r = DEFAULT_RATING, 
                rd = DEFAULT_RD, 
                last_updated = tz_pacific.localize(datetime(2000,1,1))):
        self.name = name
        self.rating = r
        self.RD = rd
        self.last_updated = last_updated
    
    def __repr__(self):
        return "{0}\nrating:{1}\nRD:{2}\nlast_updated:{3}".format(
            self.name, self.rating, self.RD, self.last_updated.strftime('%m/%d/%Y'))
    
    def _dsq(self,other_competitors):
        r = self.rating
        def summand(r_j, RD_j):
            return g(RD_j)**2*E_s(r, r_j, RD_j)*(1-E_s(r,r_j,RD_j))
        summands = [summand(j.rating, j.RD) for j in other_competitors]
        return (q**2 * sum(summands))**-1
    
    def _updated_rating(self, others, results, d2):
        def summand(r_j, RD_j, s_j):
            return g(RD_j)*(s_j - E_s(self.rating, r_j, RD_j))
        multiplier = q/(float(1)/(self.RD**2) + float(1)/d2)
        summands = [summand(j.rating, j.RD, s_j) for 
                            j, s_j in zip(others, results)]
        new_rating = self.rating + multiplier*sum(summands)
        return new_rating
    
    def _updated_RD(self, d2):
        new_RD = sqrt((float(1)/(self.RD**2) + float(1)/d2)**-1)
        date_now = tz_utc.localize(datetime.utcnow())
        t = (date_now - self.last_updated).days
        new_RD = sqrt(new_RD**2 + (c**2) * t)
        return max(min(new_RD,350),30)
    
    def updated_metrics(self, others, results, dates):
        self.last_updated = max(self.last_updated,max(dates)) if dates else self.last_updated
        if others:
            d2 = self._dsq(others)
            new_r = self._updated_rating(others, results, d2)
            new_RD = self._updated_RD(d2)
            return new_r, new_RD, self.last_updated
        else:
            return self.rating, self.RD, self.last_updated
    
    def update(self, new_r, new_RD):
        self.rating = new_r
        self.RD = new_RD


class Match(object):
    def __init__(self, day, player1, player2, winner):
        self.date = day
        self.players = [player1, player2]
        if winner.name not in [p.name for p in self.players]:
            raise ValueError
        self.winner = winner
        self.applied = 0
        
    def update_rankings(self):
        if not self.applied:
            new_r1, new_RD1 = self.player1.updated_metrics(
                [self.player2], [1*(self.player1==self.winner)]
            )
            new_r2, new_RD2 = self.player2.updated_metrics(
                [self.player1], [1*(self.player2==self.winner)]
            )
            self.player1.update(new_r1, new_RD1)
            self.player2.update(new_r2, new_RD2)
    
    def get_match_data(self,player_name):
        player_names = [p.name for p in self.players]
        if player_name not in player_names:
            raise ValueError
        def get_other_player():
            """ list is of length two, so treat the index as a boolean and negate
                to get the index of the other player in self.players"""
            return self.players[1 - player_names.index(player_name)]
        return get_other_player(), 1*(self.winner.name == player_name), self.date
            

class RatingPeriod(object):
    def __init__(self):
        self.competitors = {}
        self.matches = []
        
    def add_competitor(self,competitor):
        if not self.competitors.get(competitor.name, False):
            self.competitors[competitor.name] = {}
            self.competitors[competitor.name]['Competitor'] = competitor
            self.competitors[competitor.name]['matches'] = []
            self.competitors[competitor.name]['results'] = []
            self.competitors[competitor.name]['dates'] = []
    
    def add_match(self,match):
        self.matches.append(match)
    
    def _apply_results(self):
        for m in self.matches:
            player_names = [p.name for p in m.players]
            for p in player_names:
                opponent, result, match_date = m.get_match_data(p)
                self.competitors[p]['matches'].append(opponent)
                self.competitors[p]['results'].append(result)
                self.competitors[p]['dates'].append(match_date)
    
    def make_new_rankings(self):
        self._apply_results()
        print 'applied results!!'
        for c in self.competitors.iterkeys():
            new_r, new_RD, new_last_updated = self.competitors[c]['Competitor'].updated_metrics(
                                self.competitors[c]['matches'],
                                self.competitors[c]['results'],
                                self.competitors[c]['dates'])
            new_competitor = Competitor(c, new_r, new_RD, new_last_updated)
            self.competitors[c]['new_metrics'] = new_competitor


if __name__ == "__main__":
    date_played = tz_pacific.localize(datetime(2015,11,18))
    other_1 = Competitor('Alice',1400,30,date_played)
    other_2 = Competitor('Bob',1550,100,date_played)
    other_3 = Competitor('Charlie',1700,300,date_played)
    player0 = Competitor('Dana',1500,200,date_played)
    match1 = Match(date_played, other_1, player0, player0)
    match2 = Match(date_played, other_2, player0, other_2)
    match3 = Match(date_played, other_3, player0, other_3)
    
    rp = RatingPeriod()
    for comp in [other_1, other_2, other_3, player0]:
        rp.add_competitor(comp)
    for mtch in [match1, match2, match3]:
        rp.add_match(mtch)        
    rp.make_new_rankings()
    for c in rp.competitors.iterkeys():
        print rp.competitors[c]['new_metrics'], "\n"