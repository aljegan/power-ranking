# power-ranking

This repository provides a basic structure to implement a [glicko rating system](http://www.glicko.net/glicko/glicko.pdf). The ranking_utils module provides the core functionality of the glicko algorithm while update_rankings interfaces with google drive using [gspread](https://github.com/burnash/gspread)


## ranking_utils

### Competitor

Instances of the Competitor class are initialized with a name, rating, RD, and last_updated. Instances of the competitor can calculate updated metrics for themselves if given a list of opponents and results.

### Match

Instances of the Match class store basic data on a match. A match may update player ratings. This allows for easy use of updates on the fly. Additionally, the get_match_data() function is useful for retrieving data with which to update a Competitor instance.

### RatingPeriod

Initial as RatingPeriod(). Add competitors with add_competitor(). Add matches with add_match(). make_new_rankings() will add a 'new_metrics' key to every dictionary in rp.competitors with a new Competitor instance for each. This is used, primarily to recover the new Competitors without changing the original Competitors (otherwise, order of updating would matter).

## update_rankings

Connects to the google sheet using gspread. See [github repo](https://github.com/burnash/gspread) for how to set up a connection.

After connecting, it initializes a RatingPeriod instance. From here, it reads the "Ratings" sheet to add competitors to the rating period. Then, it reads the "Results" sheet to add the matches. From here, it calculates updated metrics for each competitor and rewrites the Rankings sheet with the new metrics. Additionally, it wipes the "Results" sheet and puts the entries into "Archived Results"
