$(function() {
    /* Settings */
    var ELECTORAL_VOTES_TO_WIN = 270;
    var STATE_TEMPLATE = _.template($("#state-template").html());
    var TOSSUP_TEMPLATE = _.template($("#tossup-template").html());
    var COMBO_GROUP_TEMPLATE = _.template($("#combo-group-template").html());
    var HISTOGRAM_TEMPLATE = _.template($("#histogram-template").html());
    var MUST_WIN_TEMPLATE = _.template($("#must-win-template").html());
    var BLOG_POST_TEMPLATE = _.template($("#blog-post-template").html());
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
    var SHOW_TOOLTIPS = !('ontouchstart' in document.documentElement);
    var MAX_STATES_FOR_WIDE_MODE = 12;
    var MIN_VOTES_FOR_WIDE_MODE = 240;
    var MAX_COMBO_GROUP = 7;
    var POLLING_INTERVAL = 1000;
    var FORCE_WIDE_MODE = false;

    if (!SHOW_TOOLTIPS) { $("body").addClass("touch-device"); } else { $("body").addClass("no-touch"); }

    /* Global state */
    var wide_mode = false;

    /* Elements */
    var electris_el = $("#electris");
    var electris_skinny_el = $("#electris-skinny");
    var incoming_el = $("#incoming");
    var maincontent_el = $("#maincontent");
    var red_candidate_el = $(".candidate.red");
    var blue_candidate_el = $(".candidate.blue");
    var red_bucket_el = red_candidate_el.find(".bucket");
    var blue_bucket_el = blue_candidate_el.find(".bucket");
    var red_tossups_el = red_candidate_el.find(".tossups");
    var blue_tossups_el = blue_candidate_el.find(".tossups");
    var red_histogram_el = red_candidate_el.find(".histogram");
    var blue_histogram_el = blue_candidate_el.find(".histogram");
    var red_combinations_el = red_candidate_el.find(".combinations");
    var blue_combinations_el = blue_candidate_el.find(".combinations");

    /* State data */
    var states = [];
    var states_by_id = {};
    var red_votes = 0;
    var blue_votes = 0;
    var total_tossup_states = 0;

    /* User data */
    var tossup_picks = {};

    /* DATA PROCESSING & RENDERING */
    
    function add_state(state) {
        var el = $(STATE_TEMPLATE({
            state: state
        }));

        if (state.call === "r") {
            red_bucket_el.append(el);
        } else if (state.call === "d") {
            blue_bucket_el.append(el);
        } else if (state.id in tossup_picks) {
            if (tossup_picks[state.id] === "r") {
                red_bucket_el.append(el);
            } else {
                blue_bucket_el.append(el);
            }
        }
        
        if (SHOW_TOOLTIPS) {
            el.find("i").tooltip({});
        }
    }

    function add_states() {
        /*
         * Add states to the tetris graph in an organized fashion.
         */
        var red_called = [];
        var red_solid = [];
        var red_leans = [];
        var red_predicted = [];
        var blue_called = [];
        var blue_solid = [];
        var blue_leans = [];
        var blue_predicted = [];

        // Group states together
        _.each(states, function(state) {
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
        });
        
        // Clear old state graphics
        $(".state").remove();

        // Add states by groups
        _.each([red_called, blue_called, red_solid, blue_solid, red_leans, blue_leans, red_predicted, blue_predicted], function(states_group) {
            // Sort by votes *top to bottom*
            states_group.reverse();

            _.each(states_group, function(state) {
                add_state(state);
            });
        });
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

        _.each(states, function(state) {
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
        });

        function sum_votes(states_group) {
            return _.reduce(states_group, function(count, state) { return count + state.electoral_votes; }, 0);
        }

        var red_votes_called = sum_votes(states_called_red);
        var red_votes_user = sum_votes(states_user_red);
        red_votes = red_votes_called + red_votes_user;
        $(".red-votes").text(red_votes);
        $(".red-needs").text(Math.max(0, ELECTORAL_VOTES_TO_WIN - red_votes));
        red_candidate_el.toggleClass("winner", red_votes >= ELECTORAL_VOTES_TO_WIN);

        var blue_votes_called = sum_votes(states_called_blue);
        var blue_votes_user = sum_votes(states_user_blue);
        blue_votes = blue_votes_called + blue_votes_user;
        $(".blue-votes").text(blue_votes);
        $(".blue-needs").text(Math.max(0, ELECTORAL_VOTES_TO_WIN - blue_votes));
        blue_candidate_el.toggleClass("winner", blue_votes >= ELECTORAL_VOTES_TO_WIN);


        // Potentially flip modes
        old_wide_mode = wide_mode;

        wide_mode = FORCE_WIDE_MODE || (
            states_not_called.length <= MAX_STATES_FOR_WIDE_MODE &&
            (red_votes >= MIN_VOTES_FOR_WIDE_MODE || blue_votes >= MIN_VOTES_FOR_WIDE_MODE)
        );

        if (wide_mode) {
            electris_skinny_el.hide();
            incoming_el.hide();
            electris_el.show();
        }

        resize_buckets();

        if (wide_mode && generate_combos) {
            generate_winning_combinations(states_not_called);
        }
    }

    function resize_buckets() {
        /*
         * Resize state buckets.
         */
        var window_width = maincontent_el.width();
        var bucket_columns = 10;

        if (wide_mode) {
            if (window_width >= 1170) {
                bucket_columns = 15;
            }
        } else {
        }

        var default_height = ELECTORAL_VOTES_TO_WIN / bucket_columns;
        var vote_height = Math.ceil(Math.max(red_votes, blue_votes) / bucket_columns)
        var height = Math.max(default_height, vote_height);
        $(".bucket").css("height", height + "em");

        // position 270 line

        if (wide_mode) {
            var header_height = 3;
            
            if (window_width == 724) {
                header_height = 4;
            } else if (window_width < 724) {
                header_height = 8;
            }
        } else {
            // TODO -- skinny responsive
            var header_height = 4;

        }

    	var line_height = .1;

        if ($.browser.msie) {
            var line_top = header_height + default_height; 
        } else {
    	    var line_top = header_height + height - default_height + line_height;
        }

    	var bucket_pos = $('.bucket.blue').position();
    	var bucket2_pos = $('.bucket.red').position();
    	var line_left = 0;
    	var line_width = '100%';

        if (wide_mode) {
            if (window_width >= 724) {
                line_left = bucket_pos.left;
                line_width = (bucket2_pos.left + $('.bucket.red').width()) - bucket_pos.left + 'px';
            }
        } else {
            // TODO -- skinny responsive
        }

    	$('#line').css('top', line_top + 'em').css('left', line_left + 'px').width(line_width);
    }

    $(window).resize(resize_buckets);

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

        // If this is the first combo, use the primer
        if (undecided_states.length == COMBO_PRIMER.undecided_states.length) {
            red_combos = COMBO_PRIMER.red_combos;
            blue_combos = COMBO_PRIMER.blue_combos;
            red_groups = COMBO_PRIMER.red_groups;
            blue_groups = COMBO_PRIMER.blue_groups;
            red_keys = _.keys(red_groups).sort();
            blue_keys = _.keys(blue_groups).sort();
        } else {
            // NB: A sorted input list generates a sorted output list
            // from our combinations algorithm.
            combos = combinations(state_ids, 1);

            _.each(combos, function(combo) {
                var combo_votes = _.reduce(combo, function(memo, id) { return memo + states_by_id[id].electoral_votes; }, 0);

                if (combo_votes >= red_needs && red_needs > 0) {
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

                if (combo_votes >= blue_needs && blue_needs > 0) {
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
        }

        var max_red_combo_group = _.max(_.values(red_groups), function(combo_group) {
            return combo_group.length;
        });

        var max_blue_combo_group = _.max(_.values(blue_groups), function(combo_group) {
            return combo_group.length;
        });

        var max_combo_group = _.max([max_red_combo_group.length, max_blue_combo_group.length]);
        
        var window_width = $('#maincontent').width();

        function show_combos(keys, groups, root_el, base_votes) {
            var combo_groups_el = root_el.find(".combinations ul");
            combo_groups_el.empty();

            for (var key = 1; key < total_tossup_states + 1; key++) {
                var group = groups[key] || [];
                var count = group.length;
                var side = root_el.hasClass("red") ? "red" : "blue";

                // Tweak combo group display
                var histogram_el = root_el.find(".histogram ." + side + key);
                histogram_el.toggleClass("active", count > 0);

                if (window_width > 480) {
                    histogram_el.find(".bar").animate({ width: (count / max_combo_group * 100) + '%' }, 300);
                } else {
                    histogram_el.find(".bar").css({ width: (count / max_combo_group * 100) + '%' });
                }

                if (count > 0) {
                    if (key > MAX_COMBO_GROUP) {
                        var combo_group_el = combo_groups_el.find("#" + side + MAX_COMBO_GROUP);
                    } else {
                        var combo_group_el = $(COMBO_GROUP_TEMPLATE({
                            side: side,
                            key: key,
                            count: count,
                            last_group: (key == MAX_COMBO_GROUP)
                        }));
                    }
                    
                    var combo_list_el = combo_group_el.find("ul");

                    _.each(group, function(combo) {
                        var state_text = [];
                        
                        _.each(combo.combo, function(state_id, i, l) {
                            var state = states_by_id[state_id];

                            state_text.push("<strong><b>" + state.stateface + "</b> " + state.name + " (" + state.electoral_votes + ")</strong>");
                        });
						
                        var el = $("<li>" + state_text.join(" + ") + " = " + (base_votes + combo.votes) + "</li>"); 
                        
                        combo_list_el.append(el);
                    });

                    if (key <= MAX_COMBO_GROUP) {
                        combo_groups_el.append(combo_group_el);
                    }
                }
            }
        }

        var simplest_combo_length = 0;

        if (red_combos.length > 0) {
            simplest_combo_length = red_combos[0].combo.length;
        } else {
            simplest_combo_length = 0;
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

        red_candidate_el.find(".combinations .robotext").html(MUST_WIN_TEMPLATE({
            candidate: "Romney",
            simplest_combo_length: simplest_combo_length,
            votes: red_votes,
            states_won: red_states_won 
        }));

        show_combos(red_keys, red_groups, red_candidate_el, red_votes);

        if (blue_combos.length > 0) {
            simplest_combo_length = blue_combos[0].combo.length;
        } else {
            simplest_combo_length = 0;
        }

        blue_candidate_el.find(".combinations .robotext").html(MUST_WIN_TEMPLATE({
            candidate: "Obama",
            simplest_combo_length: simplest_combo_length,
            votes: blue_votes,
            states_won: blue_states_won
        }));

        show_combos(blue_keys, blue_groups, blue_candidate_el, blue_votes);
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
                add_state(states_by_id[state_id]);
            }
        // Initial selection
        } else {
            tossup_picks[state_id] = winner;
            add_state(states_by_id[state_id]);
        }

        compute_stats(true);
        
        $(this).removeClass("spinner");

        return false;
    };

    electris_el.on("click", ".histogram h4", function(event) {
        /*
         * Scroll to combos list.
         */
        $("html, body").animate({
            scrollTop: $($(this).data("target")).offset().top - 45
        }, 1000);
    });

    electris_el.on("click", ".combinations a", function(event) {
        /*
         * Scroll to top of app.
         */
        $("html, body").animate({
            scrollTop: $("#key").offset().top - 45
        }, 1000);
    });

    // Render combo groups
    _.each(_.range(1, MAX_COMBO_GROUP + 1), function(key) {
        blue_histogram_el.append(HISTOGRAM_TEMPLATE({
            side: "blue",
            key: key,
            last_group: (key == MAX_COMBO_GROUP)
        }));
        
        red_histogram_el.append(HISTOGRAM_TEMPLATE({
            side: "red",
            key: key,
            last_group: (key == MAX_COMBO_GROUP)
        }));
    });

    /* DATASET LOADING/POLLING */

    function init_states(data) {
        /*
         * Load initial state data from JSON.
         */
        states = data;

        _.each(states, function(state) { 
            // Build lookup table
            states_by_id[state.id] = state;

            if (state.prediction === "t") {
                var html = TOSSUP_TEMPLATE({
                    state: state
                });

                red_tossups_el.append(html);
                blue_tossups_el.append(html);

                total_tossup_states += 1;
            }
        });

        $(".tossups li").touchClick(tossup_click_handler);

        if (SHOW_TOOLTIPS) {
            $(".tossups li").tooltip();
        }

        add_states();
        compute_stats(true);
    }

    function update_states(data) {
        /*
         * Update state data from JSON.
         */
        var changes = false;

        console.log("updating");

        for (var i = 0; i < states.length; i++) {
            var old_state = states[i];
            var state = data[i];

            if (old_state["call"] != state["call"] ||
                old_state["dem_vote_count"] != state["dem_vote_count"] ||
                old_state["rep_vote_count"] != state["rep_vote_count"] ||
                old_state["precincts_reporting"] != state["precincts_reporting"]) {

                $(".state." + state.id).remove();
                add_state(state);

                if (old_state["call"] != state["call"]) {
                    // Uncalled
                    if (!state["call"]) {
                        console.log(state["name"] + " uncalled");
                    } else {
                        // Called
                        if (!old_state["call"]) {
                            console.log(state["name"] + " called as " + state["call"]);
                        // Changed
                        } else {
                            console.log(state["name"] + " call changed to " + state["call"] + " instead of " + old_state["call"]);
                        }
                    }
                }

                states[i] = state;

                changes = true;
            }
        }

        if (changes) {
            compute_stats(true);
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

    /* MEME TRACKER */

    var MEME_UPDATE_SECS = 60;
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
        $.getJSON('tumblr.json?t=' + (new Date()).getTime(), {}, function(posts) {
            _.each(posts, function(post) {
                var template = null;

                if (post.type === "photo") {
                    template = MEME_PHOTO_TEMPLATE;
                } else if (post.type === "quote") {
                    template = MEME_QUOTE_TEMPLATE;
                } else if (post.type === "video") {
                    template = MEME_VIDEO_TEMPLATE;
                } else if (post.type === "regular") {
                    template = MEME_REGULAR_TEMPLATE;
                }

                if (!template) {
                    return;
                }

                var html = template({
                    post: post,
                    isodate: ISODateString(new Date(post["unix-timestamp"] * 1000))
                });

                // Old
                if (post.id in posts_html) {
                    // Changed
                    if (html != posts_html[post.id]) {
                        posts_el.find("#post-" + post.id).replaceWith(html);
                    }
                    // New
                } else {
                    posts_el.prepend(html);

                    var el = posts_el.find("#post-" + post.id)

                    if (first_run) {
                        el.show();
                    } else {
                        el.slideDown(1000);
                    }

                    el.find(".tstamp").timeago();
                }

                posts_html[post.id] = html;

            });

            posts_el.find(".post:nth-child(5)").nextAll().remove();
        });
    }
    

    /* RIVER OF NEWS */
	function fetch_news() {
		$.ajax({
		    url: 'http://www.npr.org/buckets/agg/series/2012/elections/riverofnews/riverofnews.jsonp',
		    dataType: 'jsonp',
		    jsonpCallback: 'nprriverofnews',
		    success: function(data){
				if ($('#live-blog-items').length == 1) {
					window.setInterval(fetch_news, 30000); /* sub in POLLING_INTERVAL later */
				}
				update_news(data);
		    }
		})
	}
	function update_news(data) {
		var template = BLOG_POST_TEMPLATE;
		var new_news = '';
		$.each(data.news.sticky, function(j,k) {
			if (k.News.status) {
				new_news += template( { post: k.News, sticky: 'sticky' } );
			}
		});
		$.each(data.news.regular, function(j,k) {
			if (k.News.status) {
				new_news += template( { post: k.News, sticky: '' } );
			}
		});
		$('#live-blog-items').empty().append(new_news);
		jQuery("p.timeago").timeago();
	}
	

	// Kickoff!
    fetch_states();
    fetch_news();
    update_memetracker(true);
    setInterval(update_memetracker, MEME_UPDATE_SECS * 1000);
});
