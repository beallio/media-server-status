var api_base_url = $SCRIPT_ROOT + "/api/" ;


// Enable Expand/Collapse panels
function toggleSlides(){
    $('.toggler').click(function(e){
        var id=$(this).attr('id');
        var widgetId=id.substring(id.indexOf('-')+1,id.length);
        $('#'+widgetId).slideToggle();
    });
}
$(function(){
    toggleSlides();
});

// Auto refresh elements
(function($)
{
    $(document).ready(function()
    {
        $.ajaxSetup(
        {
            cache: false
        });

        var $systeminfo = $(".system-info");
        var $storage = $(".storage");
        var $weather = $(".weather");

        function get_server_ip() {
            $.getJSON( api_base_url + "ip_address", function(data)
                {
                $("#server_ip").text(data.wan_ip);
                }) ;
        }

        function get_client_ip() {
            $.getJSON( 'http://api.hostip.info/get_json.php', function(data)
                {
                $("#client_ip").text(data.ip);
                }) ;
        }

        function update_ping() {
            $.getJSON( api_base_url + "ping", function(data)
                {
                $("#ping").text(data.ping + " ms");
                }) ;
        }

       function update_network_speed() {
            var $downspeed = $("#download");
            var $downspeed_progressbar = $("#progress-bar-down");
            var $upspeed = $("#upload");
            var $upspeed_progressbar = $("#progress-bar-up");
            $.getJSON( api_base_url + "network_speed", function(data) {
                var up = data.up.toFixed(2);
                var down = data.down.toFixed(2);
                $downspeed.text(down + " Mbps");
                $upspeed.text(up + " Mbps");
                var down_progressbar_width = down * (10 / 6);
                var up_progressbar_width = up * (10 / 6);
                $downspeed_progressbar.css("width", down_progressbar_width + "%");
                $upspeed_progressbar.css("width", up_progressbar_width  + "%");
            }) ;
       };

       function on_local_network(url) {
            var client_ip = getJson('http://api.hostip.info/get_json.php').ip;
            var server_ip = getJson(api_base_url + "ip_address").wan_ip;
            console.log(client_ip, server_ip, client_ip === server_ip);
            return client_ip === server_ip;
       };

        // Load at start of page
        $systeminfo.load("html/system_info");
        $storage.load("html/storage");
        $weather.load("html/weather");
        update_network_speed();
        update_ping();
        get_server_ip();
        get_client_ip();

        // Refresh every 30 seconds
        var refreshId = setInterval(function()
        {
            $systeminfo.load("html/system_info")
            $weather.load("html/weather");
        }, 30000);

        // Refresh every 1 minute
        var refreshId = setInterval(function()
        {
            update_network_speed();
            update_ping();
        }, 60000);

        // Refresh every 10 minutes
        var refreshId = setInterval(function()
        {
            get_server_ip();
            get_client_ip();
            $storage.load("html/storage");
            $weather.load("html/weather");
        }, 600000);
    });

    
    // Enable bootstrap tooltips
    $(function () {
        $("[rel=tooltip]").tooltip();
        $("[rel=popover]").popover();
        });

    $(document).ready(function() {
        $("body").tooltip({ selector: '[data-toggle=tooltip]' });
    });
})(jQuery);
