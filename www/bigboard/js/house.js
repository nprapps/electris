function nukeTarget(target){ $(target).html(''); }

$.getJSON('../../house.json', function(timezones) {

    nukeTarget('#candidates');
    var RACE_TEMPLATE = _.template($("#race-template").html());

    _.each(timezones, function(timezone){
        html = RACE_TEMPLATE({ timezone: timezone });
        $('#candidates').append(html);
    });
    $('#candidates').columnize({ columns:2 });
});