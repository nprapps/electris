$(document).ready(function(){
    
    var red = Math.floor(Math.random()*538) - 1;
    var blue = 537 - red;
    var height = Math.ceil(Math.max(red,blue)/10);
    
    _.times(red,function(){
        $("#results .bucket.red").append("<i>V</i>\n");
    });
    _.times(blue,function(){
        $("#results .bucket.blue").append("<i>V</i>\n");
    });
    
    $("#buckets,.bucket").css("height", height + "em")
});