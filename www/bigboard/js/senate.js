$(function(){
    function nukeTarget(target){ $(target).html(''); }
    function fetchData(){
        $.getJSON('../../senate.json', function(timezones) {
            var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());

            _.each(timezones, function(timezone){
                var html = TIMEZONE_TEMPLATE({ timezone: timezone });
                $('#candidates').append(html);
            });
            $('#candidates').columnize({ columns:2 });
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

   /* function refresh_countdown() {
        countdown -= 1;
        if (countdown === 0) {
            nukeTarget('#candidates');
            fetchBOP();
            fetchData();
            countdown = polling_interval + 1;
        }
    }
    setInterval(refresh_countdown, 1000);*/
});
