$(function(){
    var STATE_TEMPLATE = $("#state").html();
    
    function add_state(row) {
        var state = _.template(STATE_TEMPLATE, { state: row });

        if (row.likely === 'r'){
            $("#results .bucket.red").append(state);
        } else if(row.likely === 'd') {
            $("#results .bucket.blue").append(state);
        } else {
            $("#results #undecided").append(state);
        }

        $(".state." + row.id + " i").popover({ trigger: 'manual' }).click(function(){
            $(".state i").popover('hide');
            $(this).popover('show');
        });
    }

    function remove_state(row) {
        $("div.state." + row.id).remove();
    }

    // var red = Math.floor(Math.random()*538) - 1;
    // var blue = 537 - red;
    // var height = Math.ceil(Math.max(red,blue)/10);
    
    var ds = new Miso.Dataset({
        url : "states.csv?t=" + (new Date()).getTime(),
        delimiter: ',',
        interval: 1000,
        uniqueAgainst: 'id',
        sync: true
    });

    ds.fetch();

    ds.bind('add', function(event) {
        var red = 0;
        var blue = 0;

        _.each(event.deltas, function(delta) {
            var row = delta.changed;

            add_state(row);

            if(row.likely === 'r'){
                red += row.votes;
            } else if(row.likely ==='d') {
                blue += row.votes;
            }
        });

        var height = Math.max(27, Math.ceil(Math.max(red, blue) / 10));
        $("#buckets,.bucket").css("height", height + "em");
    });

    ds.bind('change', function(event) {
        _.each(event.deltas, function(delta) {
            _.each(_.keys(delta.old), function(key) {
                if (key === '_id') {
                    return;
                }
                
                if (delta.changed[key] != delta.old[key]) {
                    console.log('found change');
                    console.log(key)
                    console.log(delta.changed[key])
                    console.log(delta.old[key])

                    if (key === 'likely') {
                        remove_state(delta.old);
                        add_state(delta.changed);
                    }
                }
            });
        });
    });
});
