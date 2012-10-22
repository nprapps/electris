function nukeTarget(target){ $(target).html(''); }

$.getJSON('../../president.json', function(timezones) {
    nukeTarget('#candidates .full');
    var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());

    _.each(timezones, function(timezone){
        html = TIMEZONE_TEMPLATE({ timezone: timezone });
        $('#candidates .full').append(html);
    });
    $('#candidates .weighted').columnize({ columns: 2 });
    $('#candidates .full').columnize({ columns:3 });
});