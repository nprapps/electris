$(function(){
    
    // var red = Math.floor(Math.random()*538) - 1;
    // var blue = 537 - red;
    // var height = Math.ceil(Math.max(red,blue)/10);
    
    var ds = new Miso.Dataset({ url : "states.csv", delimiter: ',' });

    ds.fetch({
        success: function() {
            var red = 0;
            var blue = 0;
            this.each(function(row) {
                //$("#states").append('<li id="state-' + row.abbr + '">' + row.name + ": " + row.winner + "</li>");
                marker = "<i><span>" + row.stateface + "</span></i>\n"
                if(row.likely === 'r'){
                    _.times(row.votes, function(){$("#results .bucket.red").append(marker)});
                    red = red + row.votes;
                } else if(row.likely ==='d') {
                    _.times(row.votes, function(){$("#results .bucket.blue").append(marker)});
                    blue = blue + row.votes;
                } else {
                    _.times(row.votes, function(){$("#results #undecided").append(marker)});
                }
            });
            var height = Math.max(27, Math.ceil(Math.max(red,blue)/10));
            $("#buckets,.bucket").css("height", height + "em")
        }
    });
});