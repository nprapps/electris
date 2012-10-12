function nukeTarget(target){ $(target).html(''); }

$.getJSON('../../house.json', function(timezones) {
    nukeTarget('#candidates');
    var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());

    _.each(timezones, function(timezone){
        html = TIMEZONE_TEMPLATE({ timezone: timezone });
        $('#candidates').append(html);
    });
    $('#candidates').columnize({ columns:2 });
});