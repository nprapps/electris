$(function(){
    function nukeTarget(target){ $(target).html(''); }
    function fetchData(){
        $.getJSON('../../president.json', function(timezones) {
            var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());

            _.each(timezones, function(timezone){
                html = TIMEZONE_TEMPLATE({ timezone: timezone });
                $('#candidates .full').append(html);
            });
            $('#candidates .full').columnize({ columns:3 });
        });
    }

    fetchData();
    $('#candidates .weighted').columnize({ columns: 2 });

    var polling_interval = 15;
    var countdown = polling_interval;

  function refresh_countdown() {
        countdown -= 1;

        $("#refreshing").html(countdown+"s");

        if (countdown === 0) {
            nukeTarget('#candidates .full');
            fetchData();
            countdown = polling_interval + 1;
        }
    }

    setInterval(refresh_countdown, 1000);
});

