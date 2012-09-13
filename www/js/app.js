$(function(){
    var STATE_TEMPLATE = $("#state").html();
    var red_states = [];
    var blue_states = [];
    var undecided_states = [];
    
    function add_state(state) {
        var html = _.template(STATE_TEMPLATE, { state: state });

        if (state.likely === "r"){
            red_states.push(state);
            $("#results .bucket.red").append(html);
        } else if(state.likely === "d") {
            blue_states.push(state);
            $("#results .bucket.blue").append(html);
        } else {
            undecided_states.push(state);
            $("#results #undecided").append(html);
        }

        $(".state." + state.id + " i").popover({ trigger: "manual" }).click(function(){
            $(".state i").popover("hide");
            $(this).popover("show");
        });
    }

    function remove_state_from_array(states, state) {
        var index = 0;

        _.each(states, function(arr_state, i) {
            if (arr_state.id === state.id) {
                index = i;
            }
        });

        states.splice(index, 1);
    }

    function remove_state(state) {
        if (state.likely === "r") {
            remove_state_from_array(red_states, state);
        } else if (state.likely === "d") {
            remove_state_from_array(blue_states, state);
        } else {
            remove_state_from_array(undecided_states, state);
        }

        $("div.state." + state.id).remove();
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

    ds.fetch();

    ds.bind("add", function(event) {
        _.each(event.deltas, function(delta) {
            add_state(delta.changed);
        });

        // Sum votes
        var red_votes = _.reduce(red_states, function(memo, state) { return memo + state.votes; }, 0);
        var blue_votes = _.reduce(blue_states, function(memo, state) { return memo + state.votes; }, 0);
        var undecided_votes = _.reduce(undecided_states, function(memo, state) { return memo + state.votes; }, 0);

        //var height = Math.max(27, Math.ceil(Math.max(red_votes, blue_votes) / 10));
        $("#buckets,.bucket").css("height", 27 + "em");
    });

    ds.bind("change", function(event) {
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
                    }
                }
            });
        });
    });
});
