$(function(){
    function fetchData(){
        $.getJSON('../../house.json?t=' + (new Date()).getTime(), function(data) {
            var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());

            $('#candidates').html('');

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
    setInterval(fetchData, 15000);
});
