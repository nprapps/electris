$(function(){
    
    // var red = Math.floor(Math.random()*538) - 1;
    // var blue = 537 - red;
    // var height = Math.ceil(Math.max(red,blue)/10);
    
    var ds = new Miso.Dataset({ url : "states.csv?t=" + (new Date()).getTime(), delimiter: ',' });

    ds.fetch({
        success: function() {
            var red = 0;
            var blue = 0;
            var template = $("#state").html();
            this.each(function(row) {
                var state = _.template(template,{state:row})
                if(row.likely === 'r'){
                    $("#results .bucket.red").append(state);
                    red = red + row.votes;
                } else if(row.likely ==='d') {
                    $("#results .bucket.blue").append(state);
                    blue = blue + row.votes;
                } else {
					$("#undecided").append(state);
                }
            });
            var height = Math.max(27, Math.ceil(Math.max(red,blue)/10));
            $("#buckets,.bucket").css("height", height + "em")
            
            // $("#undecided .state").click(function(){
            //    $("#results .bucket.red").append(this);
            // });
        }
    });
});