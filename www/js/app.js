$(function(){
    var MIN_VOTES_FOR_COMBOS = 40;
    var MIN_STATES_FOR_COMBOS = 5;
    var STATE_TEMPLATE = $("#state").html();

    var state_votes = {};
    var state_names = {};
    var red_states = null;
    var red_votes = null;
    var blue_states = null;
    var blue_votes = null;
    var undecided_states = null;
    var undecided_votes = null;
    
    function add_state(state) {
        /*
         * Add the HTML for a state to the correct location.
         */
        var html = _.template(STATE_TEMPLATE, { state: state });

        if (state.likely === "sr" || state.likely === "lr"){
            $("#results .bucket.red").append(html);
        } else if(state.likely === "sd" || state.likely === "ld") {
            $("#results .bucket.blue").append(html);
        } else {
            $("#results #undecided").append(html);
        }

        $(".state." + state.id + " i").popover({ trigger: "manual" }).click(function(){
            $(".state i").popover("hide");
            $(this).popover("show");
        });
    }

    function remove_state(state) {
        /*
         * Remove the HTML for a state.
         */
        $("div.state." + state.id).remove();
    }

    function compute_stats() {
        /*
         * Compute and display vote stats.
         */
        red_states = ds.where({
            columns: ['id', 'name', 'votes'],
            rows: function(row) {
                return (row.likely === "sr" || row.likely === "lr");
            }
        });

        red_votes = red_states.sum("votes").val();
        $("#red-votes").text(red_votes);

        blue_states = ds.where({
            columns: ['id', 'name', 'votes'],
            rows: function(row) {
                return (row.likely === "sd" || row.likely === "ld");
            }
        });

        blue_votes = blue_states.sum("votes").val();
        $("#blue-votes").text(blue_votes);

        undecided_states = ds.where({
            columns: ['id', 'name', 'votes'],
            rows: function(row) {
                return (_.indexOf(["sr", "lr", "ld", "sd"], row.likely) < 0);
            }
        });

        undecided_votes = undecided_states.sum("votes").val();
        $("#undecided-votes").text(undecided_votes);
        
        generate_winning_combinations();
    }

    function generate_winning_combinations() {
        /*
         * Generate combinations of states that can win the election.
         */
        var red_needs = 270 - red_votes;
        var blue_needs = 270 - blue_votes;

        if (_.min([red_needs, blue_needs]) > MIN_VOTES_FOR_COMBOS && undecided_states.length > MIN_STATES_FOR_COMBOS) {
            $("#combos").hide();
            return;
        }

        var state_ids = undecided_states.column('id').data;

        // NB: A sorted input list generates a sorted output list
        // from our combinations algorithm.
        state_ids.sort(); 
        var combos = combinations(state_ids);

        var red_combos = [];
        var blue_combos = [];

        function is_subset(combos_so_far, new_combo) {
            return _.find(combos_so_far, function(old_combo) {
                if (new_combo.slice(0, old_combo.combo.length).toString() == old_combo.combo.toString()) {
                    return true;
                }

                return false;
            });
        }

        _.each(combos, function(combo) {
            var combo_votes = _.reduce(combo, function(memo, id) { return memo + state_votes[id]; }, 0);

            if (combo_votes > red_needs) {
                if (!is_subset(red_combos, combo)) {
                    red_combos.push({ combo: combo, votes: combo_votes });
                }
            }

            if (combo_votes > blue_needs) {
                if (!is_subset(blue_combos, combo)) {
                    blue_combos.push({ combo: combo, votes: combo_votes });
                }
            }
        });

        $("#red-combos-count").text(red_combos.length);
        $("#red-combos").empty();

        _.each(red_combos, function(combo) {
            var names = _.map(combo.combo, function(c) { return state_names[c]; });
            $("#red-combos").append("<li>" + names.join(", ") + "</li>");
        });

        $("#blue-combos-count").text(blue_combos.length);
        $("#blue-combos").empty();

        _.each(blue_combos, function(combo) {
            var names = _.map(combo.combo, function(c) { return state_names[c]; });
            $("#blue-combos").append("<li>" + names.join(", ") + "</li>");
        });
    }

    function combinations(superset) {
        /*
         * Compute all possible combinations of a given array.
         *
         * This solution was pulled from a StackOverflow answer, but I haven't
         * been able to find it again...
         */
        var result = [];
        var size = 2;

        while (size < superset.length) {          
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

    // var red = Math.floor(Math.random()*538) - 1;
    // var blue = 537 - red;
    // var height = Math.ceil(Math.max(red,blue)/10);
    
    var ds = new Miso.Dataset({
        url : "states.csv?t=" + (new Date()).getTime(),
        delimiter: ",",
        interval: 1000,
        uniqueAgainst: "id",
        sync: true
    });

    ds.fetch().then(function() {
        /*
         * After initial data load, setup stats and such.
         */
        ds.each(function(row) {
            add_state(row);

            // Build lookup tables
            state_votes[row.id] = row.votes;
            state_names[row.id] = row.name;
        });

        compute_stats();

        //var height = Math.max(27, Math.ceil(Math.max(red_votes, blue_votes) / 10));
        $("#buckets,.bucket").css("height", 27 + "em");
    });

    ds.bind("change", function(event) {
        /*
         * Process changes to state data from polling.
         */
        var real_changes = false;

        _.each(event.deltas, function(delta) {
            _.each(_.keys(delta.old), function(key) {
                if (key === "_id") {
                    return;
                }
                
                if (delta.changed[key] != delta.old[key]) {
                    console.log("found change");
                    console.log(key)
                    console.log(delta.changed[key])
                    console.log(delta.old[key])

                    if (key === "likely") {
                        remove_state(delta.old);
                        add_state(delta.changed);

                        real_changes = true;
                    }
                }
            });
        });

        if (real_changes) {
            compute_stats();
        };
    });
});
