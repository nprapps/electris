function combinations(superset, min_size, max_size) {
    /*
     * Compute all possible combinations of a given array.
     *
     * Algorithm via http://stackoverflow.com/a/4061167 
     */
    var result = [];
    var size = min_size || 1;
    var max_size = max_size || superset.length

    while (size <= max_size) {          
        var done = false;
        var current_combo = null;
        var distance_back = null;
        var new_last_index = null;
        var indexes = [];
        var indexes_last = size - 1;
        var superset_last = superset.length - 1;

        // initialize indexes to start with leftmost combo
        for (var i = 0; i < size; ++i) {
            indexes[i] = i;
        }

        while (!done) {
            current_combo = [];
            for (i = 0; i < size; ++i) {
            current_combo.push(superset[indexes[i]]);
        }

        result.push(current_combo);

        if (indexes[indexes_last] == superset_last) {
            done = true;
            for (i = indexes_last - 1; i > -1 ; --i) {
                distance_back = indexes_last - i;
                new_last_index = indexes[indexes_last - distance_back] + distance_back + 1;

                if (new_last_index <= superset_last) {
                    indexes[indexes_last] = new_last_index;
                    done = false;
                    break;
                }
            }

            if (!done) {
                ++indexes[indexes_last - distance_back];
                --distance_back;
                for (; distance_back; --distance_back) {
                    indexes[indexes_last - distance_back] = indexes[indexes_last - distance_back - 1] + 1;
                }
            }
        }
            else {++indexes[indexes_last]}
        }

        size++;
    }

    return result;
}
