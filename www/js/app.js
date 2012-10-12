$(function() {
    /* Settings */
    var ELECTORAL_VOTES_TO_WIN = 270;
    var STATE_TEMPLATE = _.template($("#state-template").html());
    var TOSSUP_TEMPLATE = _.template($("#tossup-template").html());
    var COMBO_GROUP_TEMPLATE = _.template($("#combo-group-template").html());
    var COMBO_TEMPLATE = _.template($("#combo-template").html());
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
    var red_bucket_el = $(".bucket.red");
    var blue_bucket_el = $(".bucket.blue");
    var tossups_el = $("#tossups");
    var red_combos_el = $("#red-combos");
    var blue_combos_el = $("#blue-combos");
    var red_histogram_el = $(".histogram.red");
    var blue_histogram_el = $(".histogram.blue");

    /* State data */
    var states_by_id = {};
    var alerted_states = {
        "r": [],
        "d": []
    };

    var red_votes = 0;
    var blue_votes = 0;

    /* User data */
    var user_picks = [];

    /* DATA PROCESSING & RENDERING */
    
    function add_state(state) {
        var html = STATE_TEMPLATE({
            state: state,
            user_pick: $.inArray(state.id, user_picks)
        });

        if ($.inArray(state.id, user_picks) >= 0) {
            red_bucket_el.append(html);
            blue_bucket_el.append(html);
        } else {
            if (state.prediction === "sr" || state.prediction === "lr") {
                red_bucket_el.append(html);
            } else if (state.prediction === "sd" || state.prediction === "ld") {
                blue_bucket_el.append(html);
            }
        }
    }

    function add_states() {
        /*
         * Add states to the tetris graph in an organized fashion.
         */
        var red_solid = [];
        var red_leans = [];
        var red_predicted = [];
        var blue_solid = [];
        var blue_leans = [];
        var blue_predicted = [];

        // Group states together
        states_dataset.each(function(state) {
            if (state.prediction == "sr") {
                red_solid.push(state);
            } else if (state.prediction == "sd") {
                blue_solid.push(state);
            } else if (state.prediction == "lr") {
                red_leans.push(state);
            } else if (state.prediction == "ld") {
                blue_leans.push(state);
            } else if ($.inArray(state.id, user_picks) >= 0) {
                red_predicted.push(state);
                blue_predicted.push(state);
            } 
        });

        // Clear old state graphics
        $(".state").remove();

        // Add states by groups
        _.each([red_solid, blue_solid, red_leans, blue_leans, red_predicted, blue_predicted], function(states) {
            // Sort alphabetically from *top to bottom*
            states.reverse();

            _.each(states, function(state) {
                add_state(state);
            });
        });
    }

    function remove_state(state) {
        /*
         * Remove the HTML for a state.
         */
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
            } else if ($.inArray(state.id, user_picks) >= 0) {
                states_user_red.push(state);
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
        red_votes = red_votes_fixed + red_votes_user;
        $("#p-red-electoral").text(red_votes);
        $("#p-red-call .value").text(red_votes_fixed);
        $("#p-red-predict .value").text(red_votes_user);

        var blue_votes_fixed = sum_votes(states_fixed_blue);
        var blue_votes_user = sum_votes(states_user_blue);
        blue_votes = blue_votes_fixed + blue_votes_user;
        $("#p-blue-electoral").text(blue_votes);
        $("#p-blue-call .value").text(blue_votes_fixed);
        $("#p-blue-predict .value").text(blue_votes_user);

        resize_buckets();

        var now = new Date();
        if (generate_combos) {
            generate_winning_combinations(states_not_predicted);
        }
        var elapsed = (new Date()) - now;
        console.log(elapsed / 1000 + " elapsed");
    }

    function resize_buckets() {
        /*
         * Resize state buckets.
         */
        var window_width = $(window).width();
        var bucket_columns = 10;

        if (window_width >= 1200) {
            bucket_columns = 15;
        }

        var default_height = 270 / bucket_columns;
        var vote_height = Math.ceil(Math.max(red_votes, blue_votes) / bucket_columns)
        var height = Math.max(default_height, vote_height);
        $("#buckets .bucket.red,#buckets .bucket.blue").css("height", height + "em");
        
        // position 270 line
        var header_height = 5;
        if (window_width <= 979 && window_width >= 768) {
        	header_height = 6;
    	} else if (window_width < 768) {
        	header_height = 12;
        }
    	var line_height = .1;
    	var line_top = header_height + height - default_height + line_height;

    	var bucket_pos = $('.bucket.blue').position();
    	var bucket2_pos = $('.bucket.red').position();
    	var line_left = 0;
    	var line_width = '100%';
    	if (window_width >= 768) {
	    	line_left = bucket_pos.left;
	    	line_width = (bucket2_pos.left + $('.bucket.red').width()) - bucket_pos.left + 'px';
	    }
    	$('#line').css('top', line_top + 'em').css('left', line_left + 'px').width(line_width);
    }

    $(window).resize(resize_buckets);

    function generate_winning_combinations(undecided_states) {
        /*
         * Generate combinations of states that can win the election.
         */
        var red_needs = ELECTORAL_VOTES_TO_WIN - red_votes;
        var blue_needs = ELECTORAL_VOTES_TO_WIN - blue_votes;

        $(".candidate.red .combos").toggle(red_needs > 0);
        $(".candidate.blue .combos").toggle(blue_needs > 0);

        var state_ids = _.pluck(undecided_states, "id");

        // NB: A sorted input list generates a sorted output list
        // from our combinations algorithm.
        state_ids.sort(); 
        var combos = combinations(state_ids, 1);

        var red_combos = [];
        var blue_combos = [];
        var red_keys = [];
        var blue_keys = [];
        var red_groups = {};
        var blue_groups = {};

        function is_subset(combos_so_far, new_combo) {
            return _.find(combos_so_far, function(old_combo) {
                if (new_combo.slice(0, old_combo.combo.length).toString() === old_combo.combo.toString()) {
                    return true;
                }

                return false;
            });
        }

        _.each(combos, function(combo) {
            var combo_votes = _.reduce(combo, function(memo, id) { return memo + states_by_id[id].electoral_votes; }, 0);

            if (combo_votes > red_needs) {
                if (!is_subset(red_combos, combo)) {
                    var combo_obj = { combo: combo, votes: combo_votes };

                    red_combos.push(combo_obj);

                    var key = combo.length;

                    if (!(key in red_groups)) {
                        red_keys.push(key);
                        red_groups[key] = [];
                    }

                    red_groups[key].push(combo_obj);
                }
            }

            if (combo_votes > blue_needs) {
                if (!is_subset(blue_combos, combo)) {
                    var combo_obj = { combo: combo, votes: combo_votes };

                    blue_combos.push(combo_obj);

                    var key = combo.length;

                    if (!(key in blue_groups)) {
                        blue_keys.push(key);
                        blue_groups[key] = [];
                    }

                    blue_groups[key].push(combo_obj);
                }
            }
        });

        function needs_sentence(needs) {
            if (needs > 0) {
                return "<b>" + needs + "</b> more needed to win.";
            } else if (needs == 0) {
                return "Exactly the number of votes needed to win.";
            } else {
                return "<b>" + Math.abs(needs) + "</b> more votes than needed to win.";
            }
        }

        function show_combos(keys, groups, root_el) {
            root_el.empty();

            _.each(keys, function(key) {
                var combo_group_el = $(COMBO_GROUP_TEMPLATE({
                    key: key
                }));
                
                _.each(groups[key], function(combo) {
                    var faces = _.map(combo.combo, function(id) { return "<b>" + states_by_id[id].stateface + "</b>" });

                    var el = $("<li>" + faces.join("") + "</li>"); 
                    
                    combo_group_el.find("ul").append(el);

                    el.data(combo);
                });
                
                root_el.append(combo_group_el);
            });
        }

        $("#red-needs").html(needs_sentence(red_needs));

        if (red_needs > 0) {
            $(".red-simple-combo-length").text(red_combos[0].combo.length);

            show_combos(red_keys, red_groups, red_histogram_el);
            red_histogram_el.find("h4:eq(0)").trigger("click");
        }

        $("#blue-needs").html(needs_sentence(blue_needs));
        
        if (blue_needs > 0) {
            $(".blue-simple-combo-length").text(blue_combos[0].combo.length);
            
            show_combos(blue_keys, blue_groups, blue_histogram_el);
            blue_histogram_el.find("h4:eq(0)").trigger("click");
        }
    }

    $("#tossups li").live("click", function(click) {
        /*
         * Select or unselect a tossup state.
         */
        var state_id = $(this).data("state-id");
        var state = states_dataset.where({ rows: function(s) { return s.id == state_id } }).rowByPosition(0);

        if ($.inArray(state_id, user_picks) >= 0) {
            $(this).removeClass("active");

            user_picks = _.without(user_picks, state_id);
            remove_state(state);
        } else {
            $(this).addClass("active");

            user_picks.push(state_id);
            add_state(state);
        }

        compute_stats(true);
    });

    $(".combo-group li").live("click", function(event) {
        /*
         * Switch on all states in a combo.
         */
        var combo = $(this).data();

        _.each(combo.combo, function(state) {
            $("li[data-state-id=" + state + "]").click();
        });

        compute_stats();
    });

    /* DATASET LOADING/POLLING */

    var states_dataset = new Miso.Dataset({
		url : function() { /* have to call as a function or else the timestamp won't refresh w/ each call */
			return "states.csv?t=" + (new Date()).getTime();
		},
        delimiter: ",",
        columns: [
            { name: "polls_close", type: "time", format: "YYYY-MM-DD h:mm A" }
        ]
    });
    
    states_dataset.fetch().then(function() {
        /*
         * After initial data load, setup stats and such.
         */
        states_dataset.each(function(state) {
            // Build lookup table
            states_by_id[state.id] = state;

            if (state.prediction === "t") {
                var html = TOSSUP_TEMPLATE({
                    state: state
                });

                tossups_el.append(html);
            }
        });

        add_states();
        compute_stats(true);
    });
    
    /* SHOW/HIDE COMBO GROUPS */
    $('.histogram h4').live("click", function() {
    	var show_text = '(show paths)';
    	var hide_text = '(hide)';
    	var t = $(this).find('i');
    	if (t.text() == show_text) {
    		t.text(hide_text);
    	} else {
    		t.text(show_text);
    	}
    	$(this).next('.combo-group').slideToggle('fast').parent('li').siblings('li').find('.combo-group').slideUp('fast').siblings('h4').find('i').text(show_text);
    });
    
});
