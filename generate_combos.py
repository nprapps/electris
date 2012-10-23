#!/usr/bin/env python

from copy import copy
from itertools import combinations
import json

from util import get_database

def is_subset(combos_so_far, new_combo):
    for old_combo in combos_so_far:
        test = new_combo[:len(old_combo['combo'])]

        if old_combo['combo'] == test:
            return True

    return False

def compute_combos(undecided_states, red_needs, blue_needs):
    combos = []
    n = 1
    
    while n < len(undecided_states) + 1:
        combos.extend(combinations(undecided_states, n))
        n += 1

    red_combos = []
    blue_combos = []
    red_groups = {}
    blue_groups = {}

    for combo in combos:
        combo_votes = sum([state['electoral_votes'] for state in combo])
        combo = [state['id'] for state in combo]

        if combo_votes >= red_needs and not is_subset(red_combos, combo):
            combo_obj = {
                'combo': combo,
                'votes': combo_votes
            }

            key = len(combo)

            if key not in red_groups:
                red_groups[key] = []

            red_combos.append(combo_obj)
            red_groups[key].append(combo_obj)

        if combo_votes >= blue_needs and not is_subset(blue_combos, combo):
            combo_obj = {
                'combo': combo,
                'votes': combo_votes
            }

            key = len(combo)

            if key not in blue_groups:
                blue_groups[key] = []

            blue_combos.append(combo_obj)
            blue_groups[key].append(combo_obj)

    return {
        'undecided_states': [state['id'] for state in undecided_states],
        'red_combos': red_combos,
        'blue_combos': blue_combos,
        'red_groups': red_groups,
        'blue_groups': blue_groups
    }


def main():
    db = get_database()
    states = db.execute('SELECT * FROM states ORDER BY electoral_votes DESC').fetchall()
    
    undecided_states = []
    red_needs = 270
    blue_needs = 270

    for state in states:
        if state['prediction'] in ['sr', 'lr']:
            red_needs -= state['electoral_votes']
        elif state['prediction'] in ['sd', 'ld']:
            blue_needs -= state['electoral_votes']
        else:
            undecided_states.append(state)

    output = []

    output.append(compute_combos(undecided_states, red_needs, blue_needs))

    #for i in range(0, len(undecided_states)):
    #    some_states = copy(undecided_states)
    #    del some_states[i]
    #    output.append(compute_combos(some_states, red_needs, blue_needs))

    with open('www/js/combo_primer.js', 'w') as f:
        f.write('var COMBO_PRIMER = %s' % json.dumps(output) )

if __name__ == '__main__':
    main()
