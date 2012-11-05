$(function(){
    function fetchData(){
        $.getJSON('../../president.json?t=' + (new Date()).getTime(), function(data) {
            // Prep some template code.
            var TIMEZONE_TEMPLATE = _.template($("#timezone-template").html());
            var FEATURED_TEMPLATE = _.template($("#featured-template").html());
            var BOP_TEMPLATE = _.template($("#banner-template").html());
            
            $('#candidates .weighted, #page-1, #page-2, #page-3').html('');

            // Set up an array for featured states.
            var featured_array = [];

            // Prepare the balance of power data and template.
            var bop = data.balance_of_power;
            var html = BOP_TEMPLATE({ data: bop });

            // Write the balance of power.
            $('#banner').html(html);

            // Roll through each timezone and render the html template
            // into the initial div and fill the featured_array array.
            _.each(data.results, function(timezone){
                var html = TIMEZONE_TEMPLATE({ timezone: timezone });
                $('#candidates .initial').append(html);
                _.each(timezone.states, function(state){
                    if (state.prediction == 't'){ featured_array.push(state); }
                });
            });

            // Columnize the non-featured states.
            _.each($('.state_row'), function(row, index, list){
                var page = 1;
                if (index + 1 > 22 ) { page = 2; }
                if (index + 1 > 44) { page = 3; }
                $('#page-'+ page).append(row);
            });

            // Grab each state from the featured_array and render/display them.
            _.each(featured_array, function(state){
                var html = FEATURED_TEMPLATE({ state:state });
                $('#candidates .weighted').append(html);
            });

            // Columnize the featured states.
            $('#candidates .weighted').columnize({ columns:2 });

        });
    }

    fetchData();
    setInterval(fetchData, 15000);
    
});
