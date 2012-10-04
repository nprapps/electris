$(function() {
    /* Settings */
    var MIN_VOTES_FOR_COMBOS = 100;
    var MAX_STATES_FOR_COMBOS = 10;
    var STATE_TEMPLATE = _.template($("#state-template").html());
    var REPORTING_TEMPLATE = _.template($("#reporting-template").html());
    var COMING_UP_TEMPLATE = _.template($("#coming-up-template").html());
    var CALL_ALERT_TEMPLATE = _.template($("#call-alert-template").html());
    var IS_ELECTION_NIGHT = false;
    var POLLING_INTERVAL = 1000;
    var MIN_TETRIS_WIDTH = 480;
    var POLL_CLOSING_TIMES = [
        moment("2012-11-06T18:00:00 -0500"),
        moment("2012-11-06T19:00:00 -0500"),
        moment("2012-11-06T19:30:00 -0500"),
        moment("2012-11-06T20:00:00 -0500"),
        moment("2012-11-06T21:00:00 -0500"),
        moment("2012-11-06T22:00:00 -0500"),
        moment("2012-11-06T23:00:00 -0500"),
        moment("2012-11-07T01:00:00 -0500")
    ];

    /* Elements */
    var red_bucket = $(".bucket.red");
    var blue_bucket = $(".bucket.blue");
    var state_drop_target = $("#state-drop");
    var alerts = $("#alert-msg div");

    /* State data */
    var state_votes = {};
    var state_names = {};
    var alerted_states = {
        "r": [],
        "d": []
    };

    /* User data */
    var user_predictions = {};

    /* Drag and drop */
    var original_selectstart = document.onselectstart;
    var dragging = false;
    var dragging_new = true;
    var dragging_state = null;
    var dragging_offset_x = 0;
    var dragging_offset_y = 0;

    /* Popovers */
    var popActive;
    var popIsVisible = false;
    var popClickedAway = false;

    /* DATA PROCESSING & RENDERING */
    
    function add_state(state) {
        /*
         * Add the HTML for a state to the correct location.
         */
        // Called!
        if (state.call) {
             var html = REPORTING_TEMPLATE({
                state: state
            });

            $("#pres-called").append(html);
           // TODO
        // Coming in!
        } else if (state.precincts_reporting > 0 || moment() > state.polls_close) {
            var html = REPORTING_TEMPLATE({
                state: state
            });

            $("#pres-watching").append(html);
        // Coming up!
        } else {
            var html = COMING_UP_TEMPLATE({
                state: state
            });

            $("#pres-closing .time-" + state.polls_close.format("hhmm")).append(html);
        }

        // If not rendering the tetris view then bail out
        if ($(window).width() < MIN_TETRIS_WIDTH ) {
            return;
        }

        var html = STATE_TEMPLATE({
            state: state,
            user_prediction: user_predictions[state.id],
            is_election_night: IS_ELECTION_NIGHT
        });

        if (IS_ELECTION_NIGHT) {
            if (state.call === "r") {
                red_bucket.append(html);
            } else if (state.call === "d") {
                blue_bucket.append(html);
            } else if (user_predictions[state.id] === "r") {
                red_bucket.append(html);
            } else if (user_predictions[state.id] === "d") {
                blue_bucket.append(html);
            }
        } else {
            if (state.id in user_predictions) {
                if (user_predictions[state.id] === "r") {
                    red_bucket.append(html);
                } else if (user_predictions[state.id] === "d") {
                    blue_bucket.append(html);
                }
            } else {
                if (state.prediction === "sr" || state.prediction === "lr") {
                    red_bucket.append(html);
                } else if (state.prediction === "sd" || state.prediction === "ld") {
                    blue_bucket.append(html);
                }
            }
        }

        $(".state." + state.id + " i").popover({ trigger: "manual" }).click(function(e){
            $(".state i").popover("hide");
            $(this).popover("show");
            popActive = $(this);
	        popClickedAway = false;
	        popIsVisible = true;
        });
    }

    function remove_state(state) {
        /*
         * Remove the HTML for a state.
         */
        //$("#pres-results ." + state.id).remove();

        if ($(window).width() < MIN_TETRIS_WIDTH ) {
            return;
        }

        $(".state." + state.id).remove();
    }

    function compute_stats(generate_combos) {
        /*
         * Compute and display vote stats.
         */
        var states_fixed_red = [];
        var states_fixed_blue = [];
        var states_user_red = [];
        var states_user_blue = [];
        var states_not_predicted = [];

        states_dataset.each(function(state) {
            if (state.prediction === "sr" || state.prediction === "lr") {
                states_fixed_red.push(state);
            } else if (state.prediction === "sd" || state.prediction == "ld") {
                states_fixed_blue.push(state);
            } else if (state.id in user_predictions && user_predictions[state.id] === "r") {
                states_user_red.push(state);
            } else if (state.id in user_predictions && user_predictions[state.id] === "d") {
                states_user_blue.push(state);
            } else {
                states_not_predicted.push(state);
            }
        });

        function sum_votes(states) {
            return _.reduce(states, function(count, state) { return count + state.electoral_votes; }, 0);
        }

        var red_votes_fixed = sum_votes(states_fixed_red)
        var red_votes_user = sum_votes(states_user_red);
        //$("#red-votes").text(red_votes_fixed + red_votes_user);
        $("#p-red-electoral").text(red_votes_fixed + red_votes_user);
        $("#p-red-call .value").text(red_votes_fixed);
        $("#p-red-predict .value").text(red_votes_user);

        var blue_votes_fixed = sum_votes(states_fixed_blue);
        var blue_votes_user = sum_votes(states_user_blue);
        //$("#blue-votes").text(blue_votes_called);
        $("#p-blue-electoral").text(blue_votes_fixed + blue_votes_user);
        $("#p-blue-call .value").text(blue_votes_fixed);
        $("#p-blue-predict .value").text(blue_votes_user);

        //unpredicted_votes = sum_votes(states_not_predicted);
        //$("#undecided-votes").text();

        //total_votes = red_votes_called + blue_votes_called + not_called_votes;
        //$('#o-president').find('.blue b').width(((blue_votes_called / total_votes) * 100) + '%');
        //$('#o-president').find('.red b').width(((red_votes_called / total_votes) * 100) + '%');

        if ($(window).width() >= MIN_TETRIS_WIDTH ) {
            var height = Math.max(27, Math.ceil(Math.max(red_votes_fixed + red_votes_user, blue_votes_fixed + blue_votes_user) / 10));
            $("#buckets,#buckets .red,#buckets .blue").css("height", height + "em");
        }

        if (generate_combos) {
            generate_winning_combinations(red_votes_fixed, blue_votes_fixed, states_not_predicted);
        }
    }

    function update_bucket_height() {
        /*
         * Set the height of the tetris buckets to either 270 votes or higher if
         * we've already passed 270.
         */
    }

    function generate_winning_combinations(red_votes, blue_votes, undecided_states) {
        /*
         * Generate combinations of states that can win the election.
         */
        var red_needs = 270 - red_votes;
        var blue_needs = 270 - blue_votes;

        if ((red_needs > MIN_VOTES_FOR_COMBOS && blue_needs > MIN_VOTES_FOR_COMBOS) || undecided_states.length > MAX_STATES_FOR_COMBOS) {
            //$(".combos").hide();
            return;
        }

        //var state_ids = undecided_states.column('id').data;
        var state_ids = _.pluck(undecided_states, "id");

        // NB: A sorted input list generates a sorted output list
        // from our combinations algorithm.
        state_ids.sort(); 
        var combos = combinations(state_ids, 2);

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
                    red_combos.push({ combo: combo, votes: combo_votes, winner: "r" });
                }
            }

            if (combo_votes > blue_needs) {
                if (!is_subset(blue_combos, combo)) {
                    blue_combos.push({ combo: combo, votes: combo_votes, winner: "d" });
                }
            }
        });

        function combo_ranker(a, b) {
            if (a.combo.length > b.combo.length) {
                // a > b
                return 1;
            } else if (a.combo.length < b.combo.length) {
                // a < b
                return -1;
            } else {
                if (a.votes > b.votes) {
                    // a > b
                    return 1;
                } else if (a.votes < b.votes) {
                    // a < b
                    return -1;
                } else {
                    // a == b
                    return 0;
                }
            }
        }

        red_combos.sort(combo_ranker);
        blue_combos.sort(combo_ranker);

        var red_combo_length_counts = _.countBy(red_combos, function(combo) { return combo.combo.length; });
        var blue_combo_length_counts = _.countBy(blue_combos, function(combo) { return combo.combo.length; });

        $("#red-needs").text(red_needs);
        $(".red-simple-combo-length").text(red_combos[0].combo.length);
        $(".red-simple-combos-count").text(red_combo_length_counts[red_combos[0].combo.length]);
        $("#red-combos").empty();

        _.each(red_combos, function(combo) {
            var names = _.map(combo.combo, function(id) { return state_names[id] + " (" + state_votes[id] + ")"; });
            var total = _.reduce(combo.combo, function(memo, id) { return memo + state_votes[id]; }, 0);
            var el = $("<li>" + names.join(" + ") + " = " + total + "</li>"); 
            el.data(combo);
            $("#red-combos").append(el);
        });

        $("#blue-needs").text(blue_needs);
        $(".blue-simple-combo-length").text(blue_combos[0].combo.length);
        $(".blue-simple-combos-count").text(blue_combo_length_counts[blue_combos[0].combo.length]);
        $("#blue-combos").empty();

        _.each(blue_combos, function(combo) {
            var names = _.map(combo.combo, function(id) { return state_names[id] + " (" + state_votes[id] + ")"; });
            var total = _.reduce(combo.combo, function(memo, id) { return memo + state_votes[id]; }, 0);
            var el = $("<li>" + names.join(" + ") + " = " + total + "</li>"); 
            el.data(combo);
            $("#blue-combos").append(el);
        });
    }

    $("#blue-combos li,#red-combos li").live("click", function(event) {
        /*
         * Add win path to tetris display.
         */
        var combo = $(this).data();

        user_predictions = {};

        states_dataset.each(function(state) {
            if (state.prediction === "t") {
                if ($.inArray(state.id, combo.combo) >= 0) {
                    user_predictions[state.id] = combo.winner; 
                } else {
                    if (combo.winner === "r") {
                        user_predictions[state.id] = "d";
                    } else {
                        user_predictions[state.id] = "r";
                    }
                }
            
                remove_state(state);
                add_state(state);
            }
        });

        compute_stats();
    });

    /* DATASET LOADING/POLLING */

    var states_dataset = new Miso.Dataset({
        url : "states.csv?t=" + (new Date()).getTime(),
        delimiter: ",",
        columns: [
            { name: "polls_close", type: "time", format: "YYYY-MM-DD h:mm A" }
        ],
        interval: IS_ELECTION_NIGHT ? POLLING_INTERVAL : null,
        uniqueAgainst: "id",
        sync: true
    });
    
    states_dataset.fetch().then(function() {
        /*
         * After initial data load, setup stats and such.
         */
        states_dataset.each(function(state) {
            add_state(state);

            // Build lookup tables
            state_votes[state.id] = state.electoral_votes;
            state_names[state.id] = state.name;
        });

        compute_stats(true);
    });

    function update_call_alert() {
        /*
         * Replace current alerts with updated alerts.
         */
        $(".call-alert").remove();

        var html = CALL_ALERT_TEMPLATE({
            states: alerted_states
        });

        alerts.append(html);
    }

    $(".call-alert").live("close", function () {
        /*
         * Reset calls which have not been dismissed.
         */
        alerted_states.r = [];
        alerted_states.d = [];
    });

    states_dataset.bind("change", function(event) {
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
                    if (key === "call" || key === "dem_vote_count" || key === "rep_vote_count" || key === "precints_reporting") {
                        var old_state = delta.old;
                        var state = delta.changed;

                        remove_state(old_state);
                        add_state(state);

                        if (key === "call") {
                            // Uncalled!
                            if (!state.call) {
                                //TODO -- handle revocations
                                //alerted_states.push(caller +" has revoked its call for " + state.name + ". This state's result is undecided.");
                            } else {
                                // Called
                                if (!old_state.call) {
                                    alerted_states[state.call].push(state);
                                } else {
                                    // TODO -- handle changes
                                    // TODO -- alert for state may already appear in another list
                                    //alerted_states.push(caller + " has reversed its call for " + state.name + ". This state is now called for the " + called_for + ".");
                                    alerted_states[state.call].push(state);
                                }
                            }
                        }

                        real_changes = true;
                    }
                }
            });
        });

        if (real_changes) {
            compute_stats();
            update_call_alert();
        };
    });

    /* POPOVERS */

    /* via stackoverflow, but modified: http://stackoverflow.com/questions/8947749/how-can-i-close-a-twitter-bootstrap-popover-with-a-click-from-anywhere-else-on */
    $(document).click(function(e) {
    	if(popIsVisible && popClickedAway) {
    		popActive.popover('hide');
    		popIsVisible = popClickedAway = false;
    	} else {
    		popClickedAway = true;
    	}
    });
});
