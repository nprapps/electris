$(function() {
    /* Settings */
    var ELECTORAL_VOTES_TO_WIN = 270;
    var STATE_TEMPLATE = _.template($("#state-template").html());
    var CALLED_TEMPLATE = _.template($("#called-template").html());
    var INCOMING_TEMPLATE = _.template($("#incoming-template").html());
    var CLOSING_TEMPLATE = _.template($("#closing-template").html());
    var TOSSUP_TEMPLATE = _.template($("#tossup-template").html());
    var COMBO_GROUP_TEMPLATE = _.template($("#combo-group-template").html());
    var BLOG_POST_TEMPLATE = _.template($("#blog-post-template").html());
    var SHOW_TOOLTIPS = !('ontouchstart' in document.documentElement);
    var MAX_STATES_FOR_WIDE_MODE = 12;
    var MAX_COMBO_GROUP = 7;
    var POLLING_INTERVAL = 1000;
    var UPDATE_CLOSING_INTERVAL = 60000;
    var RIVER_TIMER = null;

    if (!SHOW_TOOLTIPS) { $("body").addClass("touch-device"); } else { $("body").addClass("no-touch"); }

    /* Global state */
    var wide_mode = false;
    var alerts = [];
    var alert_timer = null;
    var next_closing = null;
    var window_width = 0;
    var winner = null;
    var freeze_alerts = false;

    /* Elements */
    var electris_el = $("#electris");
    var electris_skinny_el = $("#electris-skinny");
    var electris_line_el = electris_el.find(".line");
    var electris_skinny_line_el = electris_skinny_el.find(".line");
    var alert_el = $(".electris-alert");
    var results_el = $("#incoming");
    var maincontent_el = $("#the-stuff");
    var red_candidate_el = $(".candidate.red");
    var blue_candidate_el = $(".candidate.blue");
    var bucket_els = $(".bucket");
    var red_bucket_el = red_candidate_el.find(".bucket");
    var red_bucket_wide_el = electris_el.find('.candidate.red').find('.bucket');
    var blue_bucket_el = blue_candidate_el.find(".bucket");
    var blue_bucket_wide_el = electris_el.find('.candidate.blue').find('.bucket');
    var red_tossups_el = red_candidate_el.find(".tossups");
    var blue_tossups_el = blue_candidate_el.find(".tossups");
    var red_histogram_el = red_candidate_el.find(".histogram");
    var blue_histogram_el = blue_candidate_el.find(".histogram");
    var red_votes_el = $(".red-votes");
    var blue_votes_el = $(".blue-votes");
    var red_needs_el = $(".red-needs");
    var blue_needs_el = $(".blue-needs");
    var called_el = $(".pres-called");
    var incoming_el = $(".pres-watching");
    var closing_el = $(".pres-closing");
    var live_blog_el = $("#live-blog-items");
    var live_blog_more_el = $('#live-blog-more');
    var combinations_modal_el = $("#combinations-modal");

    /* State data */
    var states = [];
    var states_by_id = {};
    var red_votes = 0;
    var blue_votes = 0;
    var total_tossup_states = 0;
    var polls_closing_html = {};
    var incoming_count = 0;
    var called_count = 0;

    /* User data */
    var tossup_picks = {};

    /* DATA PROCESSING & RENDERING */
    
    function add_state(state,animate) {
        /*
         * Render a single state and add it to the correct bucket(s).
         */
        var el = $(STATE_TEMPLATE({
            state: state
        }));
        //setting up a second element so that our styles get applied properly when we drop the boxes
        var el2 = $(STATE_TEMPLATE({
            state: state
        }));

        // Called states
        if (state.call) {
            if (state.call === "r") {
                $(red_bucket_el[0]).append(el);
                //like i said above, for some reason, we need to be explicit about these elements for the box dropping styles
                $(red_bucket_el[1]).append(el2);
            } else if (state.call === "d") {
                $(blue_bucket_el[0]).append(el);
                $(blue_bucket_el[1]).append(el2);
            }
            if (SHOW_TOOLTIPS) {
                el.find("i").tooltip({});
            }
            
            //happens when we're adding a new state to an existing stack of states
            if(animate){
                //IE can't swing this, so don't bother
                if(!$.browser.msie) {
                    el.addClass('fall').delay(13000).queue(function(next){
                        $(this).removeClass("fall");
                        next();
                    });
                    el2.addClass('fall').delay(13000).queue(function(next){
                        $(this).removeClass("fall");
                        next();
                    });
                }
            }
            
        // toss-up states
        } else if (state.id in tossup_picks) {
			if (tossup_picks[state.id] === "r") {
				red_bucket_wide_el.append(el);
			} else {
				blue_bucket_wide_el.append(el);
			}
        }

        el = null;
    }

    function add_states() {
        /*
         * Add states to the tetris graph in an organized fashion.
         */
        var red_called = [];
        var red_predicted = [];
        var blue_called = [];
        var blue_predicted = [];
        var states_length = states.length;

        // Group states together
        for (var i = 0; i < states_length; i++) {
            var state = states[i];
            
            if (state.call === "r") {
                red_called.push(state)
            } else if (state.call === "d") {
                blue_called.push(state)
            } else if (state.id in tossup_picks) {
                if (tossup_picks[state.id] === "r") {
                    red_predicted.push(state);
                } else {
                    blue_predicted.push(state);
                }
            }
        }
        
        // Clear old state graphics
        $(".state").remove();

        // Add states by groups
        var groups = [red_called, blue_called, red_predicted, blue_predicted];
        var groups_length = groups.length;

        for (var i = 0; i < groups_length; i++) {
            var states_group = groups[i];
            var states_group_length = states_group.length;

            // Sort by votes *top to bottom*
            states_group.reverse();

            for (var j = 0; j < states_group_length; j++) {
                add_state(states_group[j]);
            }
        }
    }

    function compute_stats(generate_combos) {
        /*
         * Compute and display vote stats.
         */
        var states_called_red = [];
        var states_called_blue = [];
        var states_user_red = [];
        var states_user_blue = [];
        var states_not_called = [];
        var states_length = states.length;

        for (var i = 0; i < states_length; i++) {
            var state = states[i];

            if (state.call === "r") {
                states_called_red.push(state);
            } else if (state.call === "d") {
                states_called_blue.push(state)
            } else if (state.id in tossup_picks) {
                if (tossup_picks[state.id] === "r") {
                    states_user_red.push(state);
                } else {
                    states_user_blue.push(state);
                }
            } else {
                states_not_called.push(state);
            }
        };

        function sum_votes(states_group) {
            return _.reduce(states_group, function(count, state) { return count + state.electoral_votes; }, 0);
        }

        var red_votes_called = sum_votes(states_called_red);
        var red_votes_user = sum_votes(states_user_red);
        red_votes = red_votes_called + red_votes_user;
        red_votes_el.text(red_votes);
        red_needs_el.text(Math.max(0, ELECTORAL_VOTES_TO_WIN - red_votes));
        red_candidate_el.toggleClass("winner", red_votes >= ELECTORAL_VOTES_TO_WIN);

        var blue_votes_called = sum_votes(states_called_blue);
        var blue_votes_user = sum_votes(states_user_blue);
        blue_votes = blue_votes_called + blue_votes_user;
        blue_votes_el.text(blue_votes);
        blue_needs_el.text(Math.max(0, ELECTORAL_VOTES_TO_WIN - blue_votes));
        blue_candidate_el.toggleClass("winner", blue_votes >= ELECTORAL_VOTES_TO_WIN);

        var old_winner = winner;

        if (red_votes_called > ELECTORAL_VOTES_TO_WIN) {
            winner = "r";
        } else if (blue_votes_called >= ELECTORAL_VOTES_TO_WIN) {
            winner = "d";
        } else {
            winner = null;
        }

        // WINNER!
        if (winner && !old_winner) {
            var alert_text = null;
            var side = null;
            
            if (winner === "d") {
                alert_text = 'NPR projects that <strong class="alert-name">Barack Obama</strong> will win re-election. <strong><b>z</b></strong>';
                side = "blue";
            } else {
                alert_text = 'NPR projects that <strong class="alert-name">Mitt Romney</strong> will win the presidency. <strong><b>z</b></strong>';
                side = "red";
            }

            alerts.push({
                body: alert_text,
                side: side,
                winner: true
            });

            update_alerts();
        // We changed our mind...
        } else if (!winner && old_winner) {
            var alert_text = null;
            var side = null;

            if (old_winner === "d") {
                alert_text = 'NPR has retracted its earlier projection that <strong class="alert-name">Barack Obama</strong> will win re-election.';
            } else {
                alert_text = 'NPR has retracted its earlier projection that <strong class="alert-name">Mitt Romney</strong> will win the presidency.';
            }
           
            // Replace any lingering alerts with just the one we care about
            alerts = [];
            alerts.push({
                body: alert_text,
                side: null,
                winner: false 
            });

            freeze_alerts = false;

            update_alerts();
        // The whole thing flips
        } else if (winner && old_winner && winner != old_winner) {
            var alert_text = null;
            var side = null;

            if (old_winner === "d") {
                alert_text = 'NPR has retracted its earlier projection that <strong class="alert-name">Barack Obama</strong> will win re-election.';
            } else {
                alert_text = 'NPR has retracted its earlier projection that <strong class="alert-name">Mitt Romney</strong> will win the presidency.';
            }
           
            // Replace any lingering alerts with just the one we care about
            alerts = [];
            alerts.push({
                body: alert_text,
                side: null,
                winner: false 
            });
            
            if (winner === "d") {
                alert_text = 'NPR projects that <strong class="alert-name">President Obama</strong> will win re-election.';
                side = "blue";
            } else {
                alert_text = 'NPR projects that <strong class="alert-name">Mitt Romney</strong> will win the presidency.';
                side = "red";
            }

            alerts.push({
                body: alert_text,
                side: side,
                winner: true
            });

            freeze_alerts = false;

            update_alerts();
        }

        // Potentially flip modes
        var old_wide_mode = wide_mode;

        wide_mode = (states_not_called.length <= MAX_STATES_FOR_WIDE_MODE) && !winner;

		// FLIP!
		if (wide_mode && !old_wide_mode) {
			$("body").addClass('wide-mode');
        // FLIP BACK!
        } else if (!wide_mode && old_wide_mode) {
            $("body").removeClass('wide-mode');
            flip_skinny_mode();
        }
        
        resize_buckets();

        if (wide_mode && generate_combos) {
            generate_winning_combinations(states_not_called);
        }
    }
    
    function flip_wide_mode() {
		electris_skinny_el.hide();
		results_el.hide();
		electris_el.show();
        resize_buckets();
        // for mobile tabs
		$("#results-wide").addClass('active');
		$("#results-tab").attr('href','#results-wide');
    }
    
    function flip_skinny_mode() {
		electris_skinny_el.show();
		results_el.show();
		electris_el.hide();
        resize_buckets();
        // for mobile tabs
		$("#results").addClass('active');
		$("#results-tab").attr('href','#results');
    }
    
    $('#wide-button').click( flip_wide_mode );
    $('#skinny-button').click( flip_skinny_mode );
    
    function resize_buckets() {
        /*
         * Resize state buckets.
         */
        window_width = maincontent_el.width();
        var bucket_columns = 10;

        var default_height = ELECTORAL_VOTES_TO_WIN / bucket_columns;
        var vote_height = Math.ceil(Math.max(red_votes, blue_votes) / bucket_columns)
        var height = Math.max(default_height, vote_height);
        bucket_els.css("height", height + "em");

		var line_height = .1;
        var header_height = 0;

        if (wide_mode) {
            
            //using the actual window.height instead of the variable we set up top
            //cuz this is based on our media queries
            header_height = 3;
            if ($(window).width() <= 979) {
                header_height = 4;
            }
            if ($(window).width() <= 767) {
                header_height = 8;
            }
            
			var bucket_pos = blue_bucket_el.position();
			var bucket2_pos = red_bucket_el.position();
			var line_left = 0;
			var line_width = '100%';
	
			if (window_width >= 724) {
				line_left = bucket_pos.left;
				line_width = (bucket2_pos.left + red_bucket_el.width()) - bucket_pos.left + 'px';
			}

            // Reinitialize bootstrap tooltips for wide bucket
            if (SHOW_TOOLTIPS) {
                $('[rel="tooltip"]').tooltip();
            }
        }

		if ($.browser.msie) {
			var line_top = header_height + default_height; 
		} else {
			var line_top = header_height + height - default_height + line_height;
		}

        if (wide_mode) {
			electris_line_el.css('top', line_top + 'em').css('left', line_left + 'px').width(line_width);
		} else {
			electris_skinny_line_el.css('top', line_top + 'em');
		}

        // Kill affix plugin for small displays
        if (window_width < 768){
            $("#results-bar").removeAttr('data-spy');
        }
    }

    $(window).resize(resize_buckets);

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

    function is_subset(combos_so_far, new_combo) {
        /*
         * Determine if one combo is a subset of any of a list of other combos.
         */
        return _.find(combos_so_far, function(old_combo) {
            if (new_combo.slice(0, old_combo.combo.length).toString() === old_combo.combo.toString()) {
                return true;
            }

            return false;
        });
    }

    function generate_winning_combinations(undecided_states) {
        /*
         * Generate combinations of states that can win the election.
         */
        var red_needs = ELECTORAL_VOTES_TO_WIN - red_votes;
        var blue_needs = ELECTORAL_VOTES_TO_WIN - blue_votes;

        var combos = [];
        var red_combos = [];
        var blue_combos = [];
        var red_keys = [];
        var blue_keys = [];
        var red_groups = {};
        var blue_groups = {};
         
        var state_ids = _.pluck(undecided_states, "id");

        // NB: A sorted input list generates a sorted output list
        // from our combinations algorithm.
        combos = combinations(state_ids, 1);
        combos_length = combos.length;

        for (var i = 0; i < combos_length; i++) {
            var combo = combos[i];
            var combo_length = combo.length;
            var combo_votes = 0;

            for (var j = 0; j < combo_length; j++) {
                combo_votes += states_by_id[combo[j]].electoral_votes;
            }

            if (combo_votes >= red_needs && red_needs > 0) {
                if (!is_subset(red_combos, combo)) {
                    var combo_obj = { combo: combo, votes: combo_votes };

                    red_combos.push(combo_obj);

                    var key = combo_length;

                    // Combine large combos into one group
                    if (key > MAX_COMBO_GROUP) {
                        key = MAX_COMBO_GROUP;
                    }

                    if (!(key in red_groups)) {
                        red_keys.push(key);
                        red_groups[key] = [];
                    }

                    red_groups[key].push(combo_obj);
                }
            }

            if (combo_votes >= blue_needs && blue_needs > 0) {
                if (!is_subset(blue_combos, combo)) {
                    var combo_obj = { combo: combo, votes: combo_votes };

                    blue_combos.push(combo_obj);

                    var key = combo_length;

                    // Combine large combos into one group
                    if (key > MAX_COMBO_GROUP) {
                        key = MAX_COMBO_GROUP;
                    }

                    if (!(key in blue_groups)) {
                        blue_keys.push(key);
                        blue_groups[key] = [];
                    }

                    blue_groups[key].push(combo_obj);
                }
            }
        }

        var max_red_combo_group = _.max(_.values(red_groups), function(combo_group) {
            return combo_group.length;
        }) || 0;

        var max_blue_combo_group = _.max(_.values(blue_groups), function(combo_group) {
            return combo_group.length;
        }) || 0;
        
        max_red_combo_group = max_red_combo_group.length || 0;
        max_blue_combo_group = max_blue_combo_group.length || 0;

        var max_combo_group = _.max([max_red_combo_group, max_blue_combo_group]);

        function show_combos(keys, groups, side, base_votes) {
            var combo_groups_el = combinations_modal_el.find("ul." + side);
            var max_group_count = 0; 
            combo_groups_el.empty();

            for (var key = 1; key < MAX_COMBO_GROUP + 1; key++) {
                var group = groups[key] || [];
                var group_length = group.length;

                var histogram_el = $(".histogram ." + side + key);
                histogram_el.toggleClass("active", group_length > 0);

                if (group_length > 0) {
                    if (window_width > 480) {
                        histogram_el.find(".bar").animate({ width: (group_length / max_combo_group * 100) + '%' }, 300);
                    } else {
                        histogram_el.find(".bar").css({ width: (group_length / max_combo_group * 100) + '%' });
                    }

                    var combo_group_el = $(COMBO_GROUP_TEMPLATE({
                        side: side,
                        key: key,
                        count: group_length,
                        last_group: (key == MAX_COMBO_GROUP)
                    }));

                    new_combo_group = true;

                    var combo_list_el = combo_group_el.find("ul");
                    var combo_els = [];

                    for (var i = 0; i < group_length; i++) {
                        var combo = group[i];
                        var combo_length = combo.combo.length;
                        var state_text = "";
                        
                        for (var j = 0; j < combo_length; j++) {
                            var state = states_by_id[combo.combo[j]];

                            state_text += "<strong><b>" + state.stateface + "</b> " + state.name + " (" + state.electoral_votes + ")</strong>";

                            if (j != combo_length - 1) {
                                state_text += " + ";
                            }
                        };
						
                        var el = $("<li>" + state_text + " = " + (base_votes + combo.votes) + "</li>"); 
                        combo_els.push(el);

                        var el = null;
                    };
                        
                    combo_list_el.append(combo_els);
                    combo_groups_el.append(combo_group_el);

                    combo_group_el = null;
                    combo_list_el = null;
                    combo_els = null;
                } else {
                    histogram_el.find(".bar").css({ width: '0%' });
                }
            }

            if (combo_groups_el.is(":empty")) {
                if (base_votes >= ELECTORAL_VOTES_TO_WIN) {
                    combo_groups_el.html("<p>All states have been selected. There are no further paths to victory.</p>");
                } else {
                    combo_groups_el.html("<p>All states have been selected. There are no further paths to victory.</p>");
                }
            }

            combo_groups_el = null;
        }

        var red_states_won = [];
        var blue_states_won = [];
        
        _.each(tossup_picks, function(winner, state_id) {
            if (winner === "r") {
                red_states_won.push(states_by_id[state_id]);
            } else if (winner === "d") {
                blue_states_won.push(states_by_id[state_id]);
            }
        });

        red_candidate_el.find(".combos .robotext").html(must_win_robotext(
            "Romney",
            "Obama",
            red_combos,
            red_votes,
            red_states_won,
            blue_votes,
            blue_states_won
        ));

        show_combos(red_keys, red_groups, "red", red_votes);

        blue_candidate_el.find(".combos .robotext").html(must_win_robotext(
            "Obama",
            "Romney",
            blue_combos,
            blue_votes,
            blue_states_won,
            red_votes,
            red_states_won
        ));

        show_combos(blue_keys, blue_groups, "blue", blue_votes);
    }

    function must_win_robotext(candidate, opponent, combos, votes, states_won, opponent_votes, opponent_won) {
        /*
         * Generate robotext describing election scenario.
         */
        // Winner
        if (votes >= 270) {
            if (states_won.length == 0) {
                return candidate + " <strong>wins</strong> the Electoral College.";
            } else {
                return "If " + candidate + " wins the states you have selected then he will <strong>win the Electoral College</strong>.";
            }
        }

        // Deadlock!
        if (votes == 269 && opponent_votes == 269) {
            return 'In this scenario, neither candidate can win the Electoral College.<br /><a href="http://www.npr.org/blogs/itsallpolitics/2012/10/31/163950264/presidential-race-what-if-there-are-two-winners" target="_blank">What happens now? &raquo;</a>';
        }

        // Loser
        if (combos.length == 0) {
            if (opponent_won.length == 0) {
                return candidate + " <strong>cannot win</strong> the Electoral College.";
            } else {
                return "If " + opponent + " wins the states you have selected then " + candidate + " <strong>cannot win</strong> the Electoral College.";
            }
        }

        // One one-state combo left
        if (combos.length == 1 && combos[0].combo.length == 1) {
            var state = states_by_id[combos[0].combo[0]];

            if (states_won.length == 0) {
                return candidate + " must win <strong><b>" + state.stateface + "</b> " + state.name + "</strong> to win the Electoral College.";
            } else {
                return "If " + candidate + " wins the states you have selected then he must win <strong><b>" + state.stateface + "</b> " + state.name + "</strong> to win the Electoral College.";
            }
        }

        // One two-state combo left
        if (combos.length == 1 && combos[0].combo.length == 2) {
            var stateA = states_by_id[combos[0].combo[0]];
            var stateB = states_by_id[combos[0].combo[1]];

            if (states_won.length == 0) {
                return candidate + " must win <strong><b>" + stateA.stateface + "</b> " + stateA.name + " and <b>" + stateB.stateface + "</b> " + stateB.name + "</strong> to win the Electoral College.";
            } else {
                return "If " + candidate + " wins the states you have selected then he must win <strong><b>" + stateA.stateface + "</b> " + stateA.name + " and <b>" + stateB.stateface + "</b> " + stateB.name + "</strong> to win the Electoral College.";
            }
        }

        if (combos.length > 0) {
            var simplest_combo_length = combos[0].combo.length;
            var longest_combo_length = combos[combos.length - 1].combo.length;
        } else {
            var simplest_combo_length = 0;
            var longest_combo_length = 0;
        }

        // Two one-state combos left
        if (longest_combo_length == 1 && combos.length == 2) {
            var states_text = "";

            _.each(combos, function(combo, i, l) {
                var state = states_by_id[combo.combo[0]];
                states_text += "<b>" + state.stateface + "</b> " + state.name;

                if (i != l.length - 1) {
                    states_text += " or ";
                }
            });

            if (states_won.length == 0) {
                return candidate + " must win <strong>" + states_text + "</strong> to win the Electoral College.";
            } else {
                return "If " + candidate + " wins the states you have selected then he must win <strong>" + states_text + "</strong> to win the Electoral College.";
            }
        }

        // Path w/o picks
        if (states_won.length == 0) {
            return candidate + " must win <strong>at least " + simplest_combo_length + " more</strong> state" + (simplest_combo_length > 1 ? "s" : "") + ".";
        }
        
        // Path w/ picks
        return "If " + candidate + " wins the states you have selected then he must win <strong>at least " + simplest_combo_length  + " more</strong> state" + (simplest_combo_length > 1 ? "s" : "") + ".";
    }
     
    var tossup_click_handler = function(event) {
        /*
         * Select or unselect a tossup state.
         */
        var state_id = $(this).data("state-id");
        var winner = $(this).parent().hasClass("red") ? "r" : "d";
        var opposite_selector = winner === "r" ? "blue" : "red";
        var other_chiclet = $(".tossups." + opposite_selector + " li[data-state-id=" + state_id + "]");

        $(this).removeClass("taken");
        $(this).addClass("active");

        other_chiclet.removeClass("active");
        other_chiclet.addClass("taken"); 
                
        $(".state." + state_id).remove();

        if (state_id in tossup_picks) {
            // Deselecting
            if (tossup_picks[state_id] === winner) {
                $(this).removeClass("active");
                other_chiclet.removeClass("taken");

                delete tossup_picks[state_id];
            // Toggling from opponent
            } else {
                tossup_picks[state_id] = winner;
                var state = _.find(states, function(s) { return s.id == state_id });
                add_state(state);
            }
        // Initial selection
        } else {
            tossup_picks[state_id] = winner;
            var state = _.find(states, function(s) { return s.id == state_id });
            add_state(state);
        }

        compute_stats(true);
        
        $(this).removeClass("spinner");

        return false;
    };

    electris_el.on("click", ".histogram h4", function(event) {
        /*
         * Scroll to combos list.
         */
        var modal_body = combinations_modal_el.find(".modal-body");
        combinations_modal_el.modal("show");

        // NB: http://api.jquery.com/scrollTop/#comment-101347923
        modal_body.scrollTop(0);

        var target = $($(this).data("target"))
        var offset = -35;

        // On small screens we jump to top of candidate list instead
        if (window_width <= 480) {
            target = target.parent().parent();
            offset = -45;
        }
        
        modal_body.animate({
            scrollTop: target.position().top + offset
        }, 1000);
    });

    /* DATASET LOADING/POLLING */

    function init_states(data) {
        /*
         * Load initial state data from JSON.
         */
        var bop = data.balance_of_power;
        states = data.states;

        var called_ul = called_el.find("ul");
        var incoming_ul = incoming_el.find("ul");
        var closing_ul = $("#closing-modal ul");
        var closing_modal_el = $("#closing-modal");
        var closing_toggle_els = $(".show-poll-closings");

        closing_toggle_els.click(function(){
            closing_modal_el.modal();
            return false;
        });

        _.each(states, function(state) { 
            // Convert poll closing time to a moment() 
            state.polls_close = moment(state.polls_close + " -0500", "YYYY-MM-DD hh:mm a Z");

            // Build lookup table
            states_by_id[state.id] = state;

            var html = TOSSUP_TEMPLATE({
                state: state
            });

            red_tossups_el.append(html);
            blue_tossups_el.append(html);

            if (!state.call) {
                total_tossup_states += 1;
            }
        });

        var alpha_states = _.sortBy(states, "name");
        var closing_times = {};
        var called_state_els = [];
        var incoming_state_els = [];

        _.each(alpha_states, function(state) {
            var red_pct = Math.round(state.rep_vote_count / (state.rep_vote_count + state.dem_vote_count) * 100);
            var blue_pct = Math.round(state.dem_vote_count / (state.rep_vote_count + state.dem_vote_count) * 100);
            
            if (red_pct) {
                red_pct = red_pct.toString() + "%";
            } else {
                red_pct = "&mdash;";
            }

            if (blue_pct) {
                blue_pct = blue_pct.toString() + "%";
            } else {
                blue_pct = "&mdash;";
            }

            var called_state_el = $(CALLED_TEMPLATE({
                state: state,
                red_pct: red_pct,
                blue_pct: blue_pct
            }));
            
            if (!state.call) {
                called_state_el.hide();
            } else {
                called_count += 1;
            }

            called_state_els.push(called_state_el);
            called_state_el = null;

            var incoming_state_el = $(INCOMING_TEMPLATE({
                state: state,
                red_pct: red_pct,
                blue_pct: blue_pct
            }));

            if (state.call || state.precincts_reporting == 0 ) {
                incoming_state_el.hide();
            } else {
                incoming_count += 1; 
            }

            incoming_state_els.push(incoming_state_el)
            incoming_state_el = null;
            
            var isodate = state.polls_close.format("YYYY-MM-DDTHH:mm:ss Z");

            if (!(isodate in closing_times)) {
                closing_times[isodate] = [];
            }

            closing_times[isodate].push(state);
        });
            
        called_ul.append(called_state_els);
        called_state_els = null;

        incoming_ul.append(incoming_state_els);
        incoming_state_els = null;

        called_el.toggle(called_count > 0);
        incoming_el.toggle(incoming_count > 0);

        var isodates = _.keys(closing_times).sort();

        _.each(isodates, function(isodate) {
            var closing_time = moment(isodate);

            var closing_html = CLOSING_TEMPLATE({
                closing_time: closing_time,
                states: closing_times[isodate]
            });

            if (!(isodate in polls_closing_html)) {
                polls_closing_html[isodate] = [];
            }

            polls_closing_html[isodate].push(closing_html);

            closing_ul.append(closing_html);
        });

        $(".tossups li").touchClick(tossup_click_handler);

        if (SHOW_TOOLTIPS) {
            $(".tossups li").tooltip();
        }

        update_next_closing();
        setInterval(update_next_closing, UPDATE_CLOSING_INTERVAL);

        update_bop(bop);
        add_states();
        compute_stats(true);
    }

    function update_next_closing() {
        /*
         * Update what poll closing time (if any) is display.
         */
        var now = moment();

        var next = _.find(_.keys(polls_closing_html).sort(), function(isodate) {
            var closing_time = moment(isodate);
            return closing_time > now;
        });

        if (next != next_closing) {
            closing_el.find("ul").html(polls_closing_html[next]);
            closing_el.show();

            next_closing = next;
        } else if (!next) {
            closing_el.hide();
        }
    }

    function update_states(data) {
        /*
         * Update state data from JSON.
         */
        var changes = false;
        var states_length = states.length;
        var bop = data.balance_of_power;
        var data = data.states;

        for (var i = 0; i < states_length; i++) {
            var old_state = states[i];
            var state = data[i];

            if (old_state["call"] != state["call"] ||
                old_state["dem_vote_count"] != state["dem_vote_count"] ||
                old_state["rep_vote_count"] != state["rep_vote_count"] ||
                old_state["precincts_reporting"] != state["precincts_reporting"]) {

                var red_pct = Math.round(state.rep_vote_count / (state.rep_vote_count + state.dem_vote_count) * 100);
                var blue_pct = Math.round(state.dem_vote_count / (state.rep_vote_count + state.dem_vote_count) * 100);
                
                if (red_pct) {
                    red_pct = red_pct.toString() + "%";
                } else {
                    red_pct = "&mdash;";
                }

                if (blue_pct) {
                    blue_pct = blue_pct.toString() + "%";
                } else {
                    blue_pct = "&mdash;";
                }

                var state_els = $("." + state.id);
                state_els.find(".red").html(red_pct); 
                state_els.find(".blue").html(blue_pct); 

                if (old_state["call"] != state["call"]) {
                    $(".state." + state.id).remove();
                    add_state(state, true);

                    // Uncalled
                    if (!state["call"]) {
                        // Show chiclet
                        $(".tossup." + state.id).show(); 

                        state_els.find(".red,.blue").removeClass("winner");

                        state_els.filter(".called").hide();
                        state_els.filter(".incoming").show();

                        called_count -= 1;
                        incoming_count += 1;
                        total_tossup_states += 1;

                        called_el.toggle(called_count > 0);
                        incoming_el.toggle(incoming_count > 0);

                        var candidate = (old_state["call"] == "d" ? "Barack Obama" : "Mitt Romney");

                        alerts.push({
                            body: 'NPR has retracted its earlier projection that <strong class="alert-name">' + candidate + '</strong> will win <strong class="alert-state"><b>' + state.stateface + '</b> ' + state.name + ' (' + state.electoral_votes + ')</strong>',
                            side: null
                        });
                    } else {
                        // Called
                        if (!old_state["call"]) {
                            // Hide chiclet
                            $(".tossup." + state.id).hide(); 

                            if (state.id in tossup_picks) {
                                delete tossup_picks[state.id];
                            }
                        
                            if (state["call"] === "r") {
                                var side = "red";
                                state_els.find(".red").addClass("winner");
                            } else {
                                var side = "blue";
                                state_els.find(".blue").addClass("winner");
                            }
                        
                            state_els.filter(".called").show();
                            state_els.filter(".incoming").hide();
        
                            called_count += 1;
                            incoming_count -= 1;
                            total_tossup_states -= 1;

                            called_el.toggle(called_count > 0);
                            incoming_el.toggle(incoming_count > 0);
                            
                            var candidate = (state["call"] == "d" ? "Barack Obama" : "Mitt Romney");
                        
                            alerts.push({
                                body: 'NPR projects that <strong class="alert-name">' + candidate + '</strong> will win <strong class="alert-state"><b>' + state.stateface + '</b> ' + state.name + ' (' + state.electoral_votes + ')</strong>',
                                side: side
                            });
                        // Changed
                        } else {
                            if (state["call"] === "r") {
                                var side = "red";
                                state_els.find(".blue").removeClass("winner");
                                state_els.find(".red").addClass("winner");
                            } else {
                                var side = "blue";
                                state_els.find(".red").removeClass("winner");
                                state_els.find(".blue").addClass("winner");
                            }
             
                            var candidate = (state["call"] == "d" ? "Barack Obama" : "Mitt Romney");
                        
                            alerts.push({
                                body: 'NPR now projects that <strong class="alert-name">' + candidate + '</strong> will win <strong class="alert-state"><b>' + state.stateface + '</b> ' + state.name + ' (' + state.electoral_votes + ')</strong>',
                                side: side
                            });
                        }
                    }
                } else {
                    if (state["precincts_reporting"] && !old_state["precincts_reporting"]) {
                        state_els.filter(".incoming." + state.id).show();
                        incoming_count += 1;

                        incoming_el.toggle(incoming_count > 0);
                    }
                }

                states[i] = state;
                states[i].polls_close = old_state.polls_close;

                changes = true;
            }
        }
        
        update_bop(bop);

        if (changes) {
            called_el.toggle(called_count > 0);

            compute_stats(true);
            update_alerts();
        };
    }

    function fetch_states() {
        /*
         * Fetch JSON data from server and apply it.
         */
        $.getJSON("states.json?t=" + (new Date()).getTime(), function(data) {
            if (states.length == 0) {
                init_states(data);

                window.setInterval(fetch_states, POLLING_INTERVAL);
            } else {
                update_states(data);
            }
        });
    }

    function update_alerts() {
        /*
         * Clear old alerts and add any new ones.
         */
        // Don't crush existing alerts
        if (alert_timer || freeze_alerts) {
            return;
        }

        if (alerts.length > 0) {
            var new_alert = alerts.shift();

            alert_el.find(".alert-wrapper").html(new_alert.body);
            alert_el.removeClass("red blue");
            alert_el.addClass(new_alert.side);
            alert_el.show();
            
            if ('winner' in new_alert && new_alert.winner) {
                freeze_alerts = true;
            }

            // Kill this alert and possibly start the next one
            alert_timer = setTimeout(function() {
                alert_timer = null;
                update_alerts();
            }, 5000);
        } else {
            alert_el.hide();
        }
    }

    /* MEME TRACKER */

    var MEME_UPDATE_SECS = 120;
    var MEME_POSTS_TO_SHOW = 5;

    var MEME_PHOTO_TEMPLATE = _.template($("#meme-photo-template").html());
    var MEME_QUOTE_TEMPLATE = _.template($("#meme-quote-template").html());
    var MEME_VIDEO_TEMPLATE = _.template($("#meme-video-template").html());
    var MEME_REGULAR_TEMPLATE = _.template($("#meme-regular-template").html());

    var posts_el = $("#memetracker .posts");
    var posts_html = {};

    function ISODateString(d) {
        function pad(n) {
            return n < 10 ? '0' + n : n
        }

        return d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate()) + 'T' + pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()) + ':' + pad(d.getUTCSeconds()) + 'Z'
    }

    function update_memetracker(first_run) {
        /*
         * Update the memetracker from our tumblr feed.
         */
        $.getJSON('tumblr.json?t=' + (new Date()).getTime(), {}, function(posts) {
            var posts_length = posts.length;
            var has_tweets = false;

            for (var i = 0; i < posts_length; i++) {
                var post = posts[i];
                var template = null;

                if (post.type === "photo") {
                    template = MEME_PHOTO_TEMPLATE;
                } else if (post.type === "quote") {
                    template = MEME_QUOTE_TEMPLATE;
                } else if (post.type === "video") {
                    template = MEME_VIDEO_TEMPLATE;
                } else if (post.type === "regular") {
                    template = MEME_REGULAR_TEMPLATE;

                    post["regular-body"] = post["regular-body"].replace('<script charset="utf-8" src="//platform.twitter.com/widgets.js" type="text/javascript"></script>', "");
                }

                if (!template) {
                    return;
                }

                var html = template({
                    post: post,
                    isodate: ISODateString(new Date(post["unix-timestamp"] * 1000))
                });
                var el = $(html);

                // Old
                if (post.id in posts_html) {
                    // Changed
                    if (html != posts_html[post.id]) {
                        el.show();
                        posts_el.find("#post-" + post.id).replaceWith(el);

                        if (post.type === "regular") {
                           has_tweets = true;
                        }
                    }
                // New
                } else {
                    posts_el.prepend(el);

                    el = null;
                    el = posts_el.find("#post-" + post.id)

                    if (first_run) {
                        el.show();
                    } else {
                        el.slideDown(1000);
                    }

                    el.find(".tstamp").timeago();
                    el = null;

                    if (post.type === "regular") {
                        has_tweets = true;
                    }
                }

                posts_html[post.id] = html;
            }

            posts_el.find(".post:nth-child(5)").nextAll().remove();

            // Render incoming tweets
            if (has_tweets && !$.browser.msie) {
                if ('widgets' in twttr ) {
                    twttr.widgets.load(posts_el[0]);
                };
            }
        });
    }

    /* RIVER OF NEWS */

    var RIVER_POLLING_INTERVAL = 60000;
	var RIVER_INCREMENT = 25;
	var RIVER_DATA = []

	function fetch_news() {
        /*
         * Fetch the latest river of news.
         */
		$.ajax({
		    url: 'http://www-cf.nprdev.org/buckets/agg/series/2012/elections/riverofnews/riverofnews.jsonp',
		    dataType: 'jsonp',
		    jsonpCallback: 'nprriverofnews',
		    success: function(data){
				if (RIVER_TIMER === null) {
					RIVER_TIMER = window.setInterval(fetch_news, RIVER_POLLING_INTERVAL);
				}
				RIVER_DATA = data;
				update_news();
		    }
		})
	}

	function update_news() {
        /*
         * Update the river of news feed.
         */
        var data = RIVER_DATA;
		var new_news = [];

		$.each(data.news.sticky, function(j, k) {
			if (k.News.status) {
				new_news.push(BLOG_POST_TEMPLATE({
                    post: k.News,
                    sticky: "sticky"
                }));
			}
		});

		$.each(data.news.regular.slice(0, RIVER_INCREMENT), function(j, k) {
			if (k.News.status) {
				new_news.push(BLOG_POST_TEMPLATE({
                    post: k.News,
                    sticky: ''
                }));
			}
		});

		live_blog_el.empty().append(new_news);
        live_blog_el.find("p.timeago").timeago();

        new_news = null;
	}
	
	live_blog_more_el.click(function() {
		RIVER_INCREMENT += 25;
		if (RIVER_INCREMENT > RIVER_DATA.news.regular.length) {
			RIVER_INCREMENT = RIVER_DATA.news.regular.length;
			$(this).hide();
		}
		update_news();
	});


    /* BALANCE OF POWER */
    function update_bop(bop) {
        $('#pres-d-total').text(bop.president.democrats.total);
        $("#pres-header .blue").toggleClass("winner", bop.president.democrats.total >= ELECTORAL_VOTES_TO_WIN)
        $('#pres-r-total').text(bop.president.republicans.total);
        $("#pres-header .red").toggleClass("winner", bop.president.republicans.total >= ELECTORAL_VOTES_TO_WIN)
        $('#pres-d-towin').text(bop.president.democrats.needed_for_majority);
        $('#pres-r-towin').text(bop.president.republicans.needed_for_majority);
        $('#sen-d-total').text(bop.senate.democrats.total);
        $('#sen-r-total').text(bop.senate.republicans.total);
        $('#sen-d-majority').text(bop.senate.democrats.needed_for_majority);
        $('#sen-r-majority').text(bop.senate.republicans.needed_for_majority);
        $('#house-d-total').text(bop.house.democrats.total);
        $('#house-r-total').text(bop.house.republicans.total);
        $('#house-d-majority').text(bop.house.democrats.needed_for_majority);
        $('#house-r-majority').text(bop.house.republicans.needed_for_majority);
    }


	// Kickoff!
    fetch_states();
    fetch_news();
    update_memetracker(true);
    setInterval(update_memetracker, MEME_UPDATE_SECS * 1000);
});
