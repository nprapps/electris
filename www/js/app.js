function add_state(row) {
    var marker = "<i class=" + row.name + "><span>" + row.stateface + "</span></i>\n"

    if (row.likely === 'r'){
        _.times(row.votes, function(){$("#results .bucket.red").append(marker)});
    } else if(row.likely === 'd') {
        _.times(row.votes, function(){$("#results .bucket.blue").append(marker)});
    } else {
        _.times(row.votes, function(){$("#results #undecided").append(marker)});
    }
}

function remove_state(row) {
    $("i." + row.name).remove();
}

$(function(){
    
    // var red = Math.floor(Math.random()*538) - 1;
    // var blue = 537 - red;
    // var height = Math.ceil(Math.max(red,blue)/10);
    
    var ds = new Miso.Dataset({
        url : "states.csv",
        delimiter: ',',
        interval: 1000,
        uniqueAgainst: 'name',
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
                    if (key === 'likely') {
                        remove_state(delta.old);
                        add_state(delta.changed);
                    }
                    console.log('found change');
                    console.log(key)
                    console.log(delta.changed[key])
                    console.log(delta.old[key])
                }
            });
        });
    });
});
