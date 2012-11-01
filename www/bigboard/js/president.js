$(function(){
    function nukeTarget(target){ $(target).html(''); }
    function fetchData(){
        $.getJSON('../../president.json', function(timezones) {
            var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());
            var FEATURED_TEMPLATE = _.template($("#featured-template").html());
            var featured_array = [];

            _.each(timezones, function(timezone){
                var html = TIMEZONE_TEMPLATE({ timezone: timezone });
                $('#candidates .full').append(html);
                _.each(timezone.states, function(state){
                    if (state.prediction == 't'){ featured_array.push(state); }
                });
            });

            _.each(featured_array, function(state){
                var html = FEATURED_TEMPLATE({ state:state });
                $('#candidates .weighted').append(html);
            });

            $('#candidates .weighted').columnize({ columns:2 });
            $('#candidates .full').columnize({ columns:3 });
        });
    }

    function fetchBOP(){
        $.getJSON('../../bop.json', function(data){
            var BOP_TEMPLATE = _.template($("#banner-template").html());
            var html = BOP_TEMPLATE({ data: data });
            $('#banner').append(html);
        });
    }

    fetchBOP();
    fetchData();

    var polling_interval = 15;
    var countdown = polling_interval;
    function refresh_countdown() {
        countdown -= 1;
        if (countdown === 0) {
            nukeTarget('#candidates .full');
            nukeTarget('#candidates .weighted');
            fetchBOP();
            fetchData();
            countdown = polling_interval + 1;
        }
    }
    setInterval(refresh_countdown, 1000);
});
