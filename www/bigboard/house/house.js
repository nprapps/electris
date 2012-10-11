$(function(){
    function nukeTarget(target){ $(target).html(''); }
    var RACE_TEMPLATE = _.template($("#race-template").html());
    nukeTarget('.candidates')
    $.getJSON('../../house.json', function(districts) {
        var i = 0;
        $.each(districts, function(index, district){
            
            //TODO: remove! debug code!
            if (Math.random() > .9) {
                district['poll_closing_time'] = '8:00';
            } else {
                district['poll_closing_time'] = '';
            }
            
            var html = RACE_TEMPLATE({
                district: district
            });
            if (i < 40) {
                $('.candidates.left').append(html);                
            } else {
                $('.candidates.right').append(html);
            }
            i++;
        });
    }); 
});