function nukeTarget(target){ $(target).html(''); }

$.getJSON('../../senate.json', function(timezones) {

    nukeTarget('#candidates');
    _.each(timezones, function(timezone){
        RACE_TEMPLATE = _.template($("#race-template").html());
        html = RACE_TEMPLATE({ timezone: timezone });
        $('#candidates').append(html);
    });
    $('#candidates').columnize({ columns:2 });
});