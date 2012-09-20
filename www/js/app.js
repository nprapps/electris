$(function() {
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

    /* FOR POPOVERS */
    var popActive;
    var popIsVisible = false;
    var popClickedAway = false;
    
    function add_state(state) {
        /*
         * Add the HTML for a state to the correct location.
         */
        var html = _.template(STATE_TEMPLATE, { state: state });

        if (state.prediction === "sr" || state.prediction === "lr"){
            $("#results .bucket.red").append(html);
        } else if(state.prediction === "sd" || state.prediction === "ld") {
            $("#results .bucket.blue").append(html);
        } else {
            $("#results #undecided").append(html);
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
        $("div.state." + state.id).remove();
    }

    function compute_stats() {
        /*
         * Compute and display vote stats.
         */
        red_states = states_dataset.where({
            columns: ["id", "name", "electoral_votes"],
            rows: function(row) {
                return (row.prediction === "sr" || row.prediction === "lr");
            }
        });

        red_votes = red_states.sum("electoral_votes").val();
        $("#red-votes").text(red_votes);

        blue_states = states_dataset.where({
            columns: ["id", "name", "electoral_votes"],
            rows: function(row) {
                return (row.prediction === "sd" || row.prediction === "ld");
            }
        });

        blue_votes = blue_states.sum("electoral_votes").val();
        $("#blue-votes").text(blue_votes);

        undecided_states = states_dataset.where({
            columns: ["id", "name", "electoral_votes"],
            rows: function(row) {
                return (_.indexOf(["sr", "lr", "ld", "sd"], row.prediction) < 0);
            }
        });

        undecided_votes = undecided_states.sum("electoral_votes").val();
        $("#undecided-votes").text(undecided_votes);

        total_votes = red_votes + blue_votes + undecided_votes;
        $('#o-president').find('.blue b').width(((blue_votes / total_votes) * 100) + '%');
        $('#o-president').find('.red b').width(((red_votes / total_votes) * 100) + '%');
        $('#o-president').find('.undecided b').width(((undecided_votes / total_votes) * 100) + '%');
        
        
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
    }

    // var red = Math.floor(Math.random()*538) - 1;
    // var blue = 537 - red;
    // var height = Math.ceil(Math.max(red,blue)/10);
    
    var states_dataset = new Miso.Dataset({
        url : "states.csv?t=" + (new Date()).getTime(),
        delimiter: ",",
        interval: 1000,
        uniqueAgainst: "id",
        sync: true
    });

    states_dataset.fetch().then(function() {
        /*
         * After initial data load, setup stats and such.
         */
        states_dataset.each(function(row) {
            add_state(row);

            // Build lookup tables
            state_votes[row.id] = row.electoral_votes;
            state_names[row.id] = row.name;
        });


        compute_stats();

        //var height = Math.max(27, Math.ceil(Math.max(red_votes, blue_votes) / 10));
        $("#buckets,.bucket").css("height", 27 + "em");
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
                    console.log("found change");
                    console.log(key)
                    console.log(delta.changed[key])
                    console.log(delta.old[key])

                    if (key === "prediction") {
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
    	$('#undecided').prepend($('#buckets').find('.state'));
    });
    /* TODO: only the picks that are based on predictions should be reset.
    	picks based on actual live results should not move. */
    	
    /* TOP TABS */
    $('#offices').find('li').click(function() {
    	var tabName = $(this).attr('id').substring(2);
    	$('#' + tabName).show().siblings('div.row').hide();
    	$(this).addClass('active').siblings('li').removeClass('active');
    });
    $('#o-president').trigger('click');
    
});
