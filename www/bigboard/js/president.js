$(function(){
    function nukeTarget(target){ $(target).html(''); }
    function fetchData(){
        $.getJSON('../../president.json', function(timezones) {
            var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());
            var FEATURED_TEMPLATE = _.template($("#featured-template").html());
            var featured_array = [];

            _.each(timezones, function(timezone){
                var html = TIMEZONE_TEMPLATE({ timezone: timezone });
                $('#candidates .initial').append(html);
                _.each(timezone.states, function(state){
                    if (state.prediction == 't'){ featured_array.push(state); }
                });
            });

            _.each(featured_array, function(state){
                var html = FEATURED_TEMPLATE({ state:state });
                $('#candidates .weighted').append(html);
            });

            _.each($('.state_row'), function(row, index, list){
                var page = 1;
                if (index + 1 > 22 ) { page = 2; }
                if (index + 1 > 44) { page = 3; }
                $('#page-'+ page).append(row);
            });

            // $('#candidates .full').columnize({ columns:3 });
            $('#candidates .weighted').columnize({ columns:2 });

        });
    }

    function fetchBOP(){
        $.getJSON('../../bop.json', function(data){
            var BOP_TEMPLATE = _.template($("#banner-template").html());
            var html = BOP_TEMPLATE({ data: data });
            $('#banner').html(html);
        });
    }

    fetchBOP();
    fetchData();

    var polling_interval = 10;
    var countdown = polling_interval;
    function refresh_countdown() {
        countdown -= 1;
        if (countdown === 0) {
            nukeTarget('#candidates .weighted');
            nukeTarget('#page-1, #page-2, #page-3');
            fetchBOP();
            fetchData();
            countdown = polling_interval + 1;
        }
    }
    setInterval(refresh_countdown, 1000);
});
