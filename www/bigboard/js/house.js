$(function(){
    function nukeTarget(target){ $(target).html(''); }
    function fetchData(){
        $.getJSON('../../house.json', function(timezones) {
            var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());

            _.each(timezones, function(timezone){
                html = TIMEZONE_TEMPLATE({ timezone: timezone });
                $('#candidates').append(html);
            });
            $('#candidates').columnize({ columns:2 });
        });
    }

    fetchData();
    $('#candidates .weighted').columnize({ columns: 2 });

    var polling_interval = 15;
    var countdown = polling_interval;

    function refresh_countdown() {
        countdown -= 1;

        $("#refreshing").html(countdown + "s");

        if (countdown === 0) {
            nukeTarget('#candidates');
            fetchData();
            countdown = polling_interval + 1;
        }
    }

    setInterval(refresh_countdown, 1000);
});

