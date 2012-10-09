#!/usr/bin/env python

from pollster import Pollster

from util import get_database, get_states, regenerate_csv

STATES = ['al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'dc', 'fl', 'ga', 'hi', 'id', 'il', 'in', 'ia', 'ks', 'ky', 'la', 'me', 'md', 'ma', 'mi', 'mn', 'ms', 'mo', 'mt', 'ne', 'nv', 'nh', 'nj', 'nm', 'ny', 'nc', 'nd', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd', 'tn', 'tx', 'ut', 'vt', 'va', 'wa', 'wv', 'wi', 'wy']


def main():
    db = get_database()
    pollster = Pollster()

    for state in STATES:
        charts = pollster.charts(topic='2012-president', state=state)

        if charts:
            chart = charts[0]
        else:
            print 'NO DATA FOR %s' % state
            continue

        obama = 0
        romney = 0

        if chart.estimates:
            for estimate in chart.estimates:
                if estimate['choice'] == "Obama":
                    obama = estimate['value']
                elif estimate['choice'] == "Romney":
                    romney = estimate['value']
        else:
            print 'NO ESTIMATES FOR %s' % state
            continue

        prediction = "t"

        if abs(obama - romney) > 15:
            if obama > romney:
                prediction = "sd"
            else:
                prediction = "sr"
        elif abs(obama - romney) > 7.5:
            if obama > romney:
                prediction = "ld"
            else:
                prediction = "lr"

        db.execute('UPDATE states SET prediction=? WHERE id=?', (prediction, state))

    db.commit()

    regenerate_csv(get_states(db))

if __name__ == "__main__":
    main()
