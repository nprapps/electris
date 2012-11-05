$(function(){
    function fetchData(){
        $.getJSON('../../house.json', function(data) {
            var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());

            _.each(data.results, function(timezone){
                var html = TIMEZONE_TEMPLATE({ timezone: timezone });
                $('#candidates').append(html);
            });
            $('#candidates').columnize({ columns:2 });
            var bop = data.balance_of_power;
            var BOP_TEMPLATE = _.template($("#banner-template").html());
            var html = BOP_TEMPLATE({ data: bop });
            $('#banner').html(html);
        });
    }

    fetchData();

    var polling_interval = 15;
    var countdown = polling_interval;

    function refresh_countdown() {
        countdown -= 1;
        if (countdown === 0) {
            $('#candidates').html('');
            fetchData();
            countdown = polling_interval + 1;
        }
    }
    setInterval(refresh_countdown, 1000);
});
