$(function() {
    /* Settings */
    var MIN_VOTES_FOR_COMBOS = 40;
    var MIN_STATES_FOR_COMBOS = 5;
    var STATE_TEMPLATE = $("#state-template").html();
    var REPORTING_TEMPLATE = $("#reporting-template").html();
    var COMING_UP_TEMPLATE = $("#coming-up-template").html();
    var IS_ELECTION_NIGHT = true;
    var POLLING_INTERVAL = 1000;
    var MIN_TETRIS_WIDTH = 480;

    /* Elements */
    var red_bucket = $(".bucket.red");
    var blue_bucket = $(".bucket.blue");
    var undecided_bucket = $(".bucket.undecided");

    /* State data */
    var state_votes = {};
    var state_names = {};
    var state_predictions = {};
    var red_states = null;
    var red_votes = null;
    var blue_states = null;
    var blue_votes = null;
    var undecided_states = null;
    var undecided_votes = null;

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
        if ($(window).width() < MIN_TETRIS_WIDTH ) {
            return;
        }

        var html = _.template(STATE_TEMPLATE, {
            state: state,
            user_prediction: user_predictions[state.id],
            is_election_night: IS_ELECTION_NIGHT
        });

        if (IS_ELECTION_NIGHT) {
            if (state.npr_call === "r") {
                red_bucket.append(html);
            } else if (state.npr_call === "d") {
                blue_bucket.append(html);
            } else if (state.npr_call === "u") {
                undecided_bucket.append(html);
            } else if (state.ap_call === "r" && state.accept_ap_call === "y") {
                red_bucket.append(html);
            } else if (state.ap_call === "d" && state.accept_ap_call === "y") {
                blue_bucket.append(html);
            // User predictions supercede AP "undecided"
            //} else if (state.ap_call === "u" && state.accept_ap_call === "y") {
            //    undecided_bucket.append(html);
            } else if (user_predictions[state.id] === "r") {
                red_bucket.append(html);
            } else if (user_predictions[state.id] === "d") {
                blue_bucket.append(html);
            } else if (user_predictions[state.id] === "t") {
                undecided_bucket.append(html);
            } else {
                undecided_bucket.append(html);
            }
        } else {
            if (state.id in user_predictions) {
                if (user_predictions[state.id] === "r") {
                    red_bucket.append(html);
                } else if (user_predictions[state.id] === "d") {
                    blue_bucket.append(html);
                } else if (user_predictions[state.id] === "t") {
                    undecided_bucket.append(html);
                }
            } else {
                if (state.prediction === "sr" || state.prediction === "lr") {
                    red_bucket.append(html);
                } else if (state.prediction === "sd" || state.prediction === "ld") {
                    blue_bucket.append(html);
                } else {
                    undecided_bucket.append(html);
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
        if ($(window).width() < MIN_TETRIS_WIDTH ) {
            return;
        }

        $(".state." + state.id).remove();
    }

    function compute_stats() {
        /*
         * Compute and display vote stats.
         */
        red_states = states_dataset.where({
            columns: ["id", "name", "electoral_votes"],
            rows: function(row) {
                if (IS_ELECTION_NIGHT) {
                    if (row.npr_call === "r") {
                        return true;
                    } else if (row.ap_call === "r" && row.accept_ap_call === "y") {
                        return true;
                    } else if (row.id in user_predictions && user_predictions[row.id] === "r") {
                        return true;
                    } else {
                        return false;
                    }
                } else {
                    if (row.id in user_predictions && user_predictions[row.id] === "r") {
                        return true;
                    }

                    return (row.prediction === "sr" || row.prediction === "lr");
                }
            }
        });

        red_votes = red_states.sum("electoral_votes").val();
        $("#red-votes").text(red_votes);

        blue_states = states_dataset.where({
            columns: ["id", "name", "electoral_votes"],
            rows: function(row) {
                if (IS_ELECTION_NIGHT) {
                    if (row.npr_call === "d") {
                        return true;
                    } else if (row.ap_call === "d" && row.accept_ap_call === "y") {
                        return true;
                    } else if (row.id in user_predictions && user_predictions[row.id] === "d") {
                        return true;
                    } else {
                        return false;
                    }
                } else {
                    if (row.id in user_predictions && user_predictions[row.id] === "d") {
                        return true;
                    }

                    return (row.prediction === "sd" || row.prediction === "ld");
                }
            }
        });

        blue_votes = blue_states.sum("electoral_votes").val();
        $("#blue-votes").text(blue_votes);

        undecided_states = states_dataset.where({
            columns: ["id", "name", "electoral_votes"],
            rows: function(row) {
                if (IS_ELECTION_NIGHT) {
                    if (row.npr_call !== "n" && row.npr_call !== "u") {
                        return false;
                    } else if (row.ap_call !== "u" && row.accept_ap_call === "y") {
                        return false;
                    } else if (row.id in user_predictions && user_predictions[row.id] !== "t") {
                        return false;
                    } else {
                        return true;
                    }
                } else {
                    if (row.id in user_predictions && user_predictions[row.id] === "t") {
                        return true;
                    }

                    return (row.prediction === "t");
                }
            }
        });

        undecided_votes = undecided_states.sum("electoral_votes").val();
        $("#undecided-votes").text(undecided_votes);

        total_votes = red_votes + blue_votes + undecided_votes;
        $('#o-president').find('.blue b').width(((blue_votes / total_votes) * 100) + '%');
        $('#o-president').find('.red b').width(((red_votes / total_votes) * 100) + '%');
        $('#o-president').find('.undecided b').width(((undecided_votes / total_votes) * 100) + '%');

        update_bucket_height();
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
                    red_combos.push({ combo: combo, votes: combo_votes });
                }
            }

            if (combo_votes > blue_needs) {
                if (!is_subset(blue_combos, combo)) {
                    blue_combos.push({ combo: combo, votes: combo_votes });
                }
            }
        });

        $("#red-needs").text(red_needs);
        $("#red-combos-count").text(red_combos.length);
        $("#red-combos").empty();

        _.each(red_combos, function(combo) {
            var names = _.map(combo.combo, function(id) { return state_names[id] + " (" + state_votes[id] + ")"; });
            var total = _.reduce(combo.combo, function(memo, id) { return memo + state_votes[id]; }, 0);
            $("#red-combos").append("<li>" + names.join(" + ") + " = " + total + "</li>");
        });

        $("#blue-needs").text(blue_needs);
        $("#blue-combos-count").text(blue_combos.length);
        $("#blue-combos").empty();

        _.each(blue_combos, function(combo) {
            var names = _.map(combo.combo, function(id) { return state_names[id] + " (" + state_votes[id] + ")"; });
            var total = _.reduce(combo.combo, function(memo, id) { return memo + state_votes[id]; }, 0);
            $("#blue-combos").append("<li>" + names.join(" + ") + " = " + total + "</li>");
        });

        $("#combos").show();
    }

    function update_bucket_height() {
        /*
         * Set the height of the tetris buckets to either 270 votes or higher if
         * we've already passed 270.
         */
        if ($(window).width() < MIN_TETRIS_WIDTH ) {
            return;
        }

        var height = Math.max(27, Math.ceil(Math.max(red_votes, blue_votes) / 10));
        $("#buckets,#buckets .red,#buckets .blue").css("height", height + "em");
    }

    $("#add-predictions").click(function() {
        /*
         * Add NPR's predictions for how states will be called.
         */
        states_dataset.each(function(state) {
            var prediction = state_predictions[state.id];

            if (prediction === "sr" || prediction === "lr") {
                user_predictions[state.id] = "r";
            } else if (prediction === "sd" || prediction === "ld") {
                user_predictions[state.id] = "d";
            } else {
                user_predictions[state.id] = "t";
            }

            remove_state(state);
            add_state(state);
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
            // On election night we save the prediction,
            // but don't use it right away
            if (IS_ELECTION_NIGHT) {
                state_predictions[state.id] = state.prediction;
                state.prediction = "t";
            }

            add_state(state);

            // Called!
            if (state.npr_call === "r" || state.npr_call === "d" || (state.accept_ap_call && (state.ap_call === "r" || state.ap_call === "d"))) {
                 var html = _.template(REPORTING_TEMPLATE, {
                    state: state
                });

                $("#pres-called").append(html);
               // TODO
            // Coming in!
            } else if (state.precincts_reporting > 0) {
                var html = _.template(REPORTING_TEMPLATE, {
                    state: state
                });

                $("#pres-watching").append(html);
            // Coming up!
            } else {
                var html = _.template(COMING_UP_TEMPLATE, {
                    state: state
                });

                $("#pres-closing").append(html);
            }

            // Build lookup tables
            state_votes[state.id] = state.electoral_votes;
            state_names[state.id] = state.name;
        });

        compute_stats();
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
                    if (key === "ap_call" || key === "accept_ap_call" || key === "npr_call" ||
                        key === "dem_vote_count" || key === "rep_vote_count" || key === "precints_reporting") {
                        var old_state = delta.old;
                        var state = delta.changed;

                        remove_state(old_state);
                        add_state(state);

                        if (key === "ap_call" && state.accept_ap_call === "y") {
                            // Uncalled!
                            if (state.ap_call === "u") {
                                alert("The Associated Press has reversed its call for " + state.name + ". This state's result is undecided.");
                            } else {
                                // Called
                                if (old_state.ap_call === "u") {
                                    alert("The Associated Press has called " + state.name + " for the " + (state.ap_call ==="r" ? "Republicans" : "Democrats") + ".");
                                } else {
                                    alert("The Associated Press has changed its call for " + state.name + ". This state is now called for the " + (state.ap_call ==="r" ? "Republicans" : "Democrats") + ".");
                                }
                            }
                        } else if (key === "npr_call") {
                            // Uncalled!
                            if (state.npr_call === "u" || state.npr_call === "n") {
                                alert("NPR has reversed its call for " + state.name + ". This state's result is undecided.");
                            } else {
                                // Called
                                if (old_state.npr_call === "u" || old_state.npr_call === "n") {
                                    alert("NPR has called " + state.name + " for the " + (state.npr_call ==="r" ? "Republicans" : "Democrats") + ".");
                                } else {
                                    alert("NPR has changed its call for " + state.name + ". This state is now called for the " + (state.npr_call ==="r" ? "Republicans" : "Democrats") + ".");
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
        };
    });

    /* DRAG AND DROP */

    function disable_text_selection() {
        /*
         * Disable all text selection.
         */
        document.onselectstart = function() { return false; }
    }

    if ($.browser.msie) {
        disable_text_selection();
    }

    function enable_text_selection() {
        /*
         * Reenable all text selection.
         */
        document.onselectstart = original_selectstart;
    }

    $(".state").live("mousedown", function(e) {
        e = e || window.event
        
        dragging_state = $(this);

        // Called states can't be moved
        if (dragging_state.hasClass("called")) {
            return;
        }

        dragging = true;
        dragging_new = true;

        // Mouse position dragging behavior is not consistent
        //var x = dragging_state.offset().left;
        //var y = dragging_state.children("i").first().offset().top;

        //dragging_offset_x = e.pageX - x;
        //dragging_offset_y = e.pageY - y;

        dragging_offset_x = 0;
        dragging_offset_y = 0;
                
        disable_text_selection();
    });

    $(document).mouseup(function(e) {
        e = e || window.event;

        if (dragging) {
            dragging = false
            
            if (!$.browser.msie) {
                enable_text_selection();
            }

            // Bail out if state was not moved
            if (dragging_new) {
                return;
            }

            function is_within(element) {
                var left = element.offset().left;
                var right = left + element.width();
                var top = element.offset().top;
                var bottom = top + element.height();

                if ((e.pageX > left) && (e.pageX < right) && (e.pageY > top) && (e.pageY < bottom)) {
                    return true;
                }
                
                return false;
            }

            var state_id = dragging_state.data("id");
            var state = states_dataset.where({ rows: function(row) {
                return (row.id == state_id);
            }}).rowByPosition(0);

            if (is_within(blue_bucket)) {
                user_predictions[state_id] = "d";
            } else if (is_within(red_bucket)) {
                user_predictions[state_id] = "r";
            } else if (is_within(undecided_bucket)) {
                user_predictions[state_id] = "t";
            }

            dragging_state.remove();
            add_state(state);
            compute_stats();
        }
    });

    $(document).mousemove(function(e) {
        e = e || window.event;

        if (dragging) {
            if (dragging_new) {
                dragging_new = false;

                var background_color = dragging_state.children("i").first().css("background-color");
                var color = dragging_state.children("i").first().css("color");

                dragging_state.detach();
                $("#states").append(dragging_state);
                
                dragging_state.css("position", "absolute");
                dragging_state.css("width", "10em");
                dragging_state.children("i").css("color", color);
                dragging_state.children("i").css("background-color", background_color);
            }

            dragging_state.css("left", e.pageX - dragging_offset_x);
            dragging_state.css("top", e.pageY - dragging_offset_y);
        }
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
    
    
    /* RESET PICKS */

    $('#resetBtn').click(function() {
        user_predictions = {};

        states_dataset.each(function(row) {
            remove_state(row);
            add_state(row);
        });

        compute_stats();
    });
    
    
    /* PRESIDENTIAL RESULTS TABS */
	$('#pres-nav').find('li').click(function() {
		$('#' + $(this).attr('id').substr(4)).show().siblings('.results').hide();
		$(this).addClass('active').siblings('li').removeClass('active');
		return false;
	});
	$('#pres-nav li:eq(1)').trigger('click');
});
