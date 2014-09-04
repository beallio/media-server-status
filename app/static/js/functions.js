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


        function update_storage_paths() {
            $.getJSON( api_base_url + "storage", function(json) {
                $.each(json.paths,function(path, value){
                    render_storage_paths(path, value);
			    });
			    $.each(json,function(path, value){
                    render_storage_paths(path, value);
			    });
            });
        }

        function render_storage_paths(path, value) {
            $("#" + path + "-storage").text(Math.round(value.pct,0) + "%");
			$("#tooltip-" + path).attr("data-original-title", value.free + " free out of " + value.total);
			$("#progressbar-" + path).css("width", value.pct + "%");
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

       function get_system_info() {
            $.getJSON( api_base_url + "system_info", function(data) {
                function get_pct(num) {
                    return Math.round(Number(num) * 100) + '%';
                };
                // Get System uptime
                var $uptime = data.uptime_formatted ;
                $("#uptime").text($uptime.days + ", " + $uptime.hours + ", " + $uptime.min );

                // Get System Memory
                $("#memory-progress-bar-base").text(data.mem_used_pct + "%");
                var $mem_available = Number(data.mem_available.toFixed(0)).toLocaleString("en-US");
                var $mem_total = Number(data.mem_total.toFixed(0)).toLocaleString("en-US");
                $("#memory-tooltip").attr("data-original-title", $mem_available + " MB free out of " + $mem_total + " MB");
                var $pb_min = $('#progress-bar-min');
                $pb_min.css("width", data.mem_bars.xmin + '%');
                $pb_min.text(data.mem_used_pct + '%');
                $("#progress-bar-mid").css("width", data.mem_bars.xmid + '%');
                $("#progress-bar-max").css("width", data.mem_bars.xmax+ '%');

                // Get Load
                var load_div = "-min-load"
                var load_div_bar = "-min-load-bar"
                load_pcts = [];
                var x;
                for (x in data.load_avg) {
                    load_pcts.push(get_pct(data.load_avg[x]));
                };
                $("#1" + load_div).text(load_pcts[0]);
                $("#1" + load_div_bar).css("width", load_pcts[0]);
                $("#5" + load_div).text(load_pcts[1]);
                $("#5" + load_div_bar).css("width", load_pcts[1]);
                $("#15" + load_div).text(load_pcts[2]);
                $("#15" + load_div_bar).css("width", load_pcts[2]);
            }) ;
       };

       function on_local_network(url) {
            var client_ip = getJson('http://api.hostip.info/get_json.php').ip;
            var server_ip = getJson(api_base_url + "ip_address").wan_ip;
            console.log(client_ip, server_ip, client_ip === server_ip);
            return client_ip === server_ip;
       };

       /* hack found here: http://pratyush-chandra.blogspot.com/2012/04/store-ajax-json-response-into.html
          Don't use on initial page load since async is set to false, lengthens page load time
       function getJson(url) {

         return JSON.parse($.ajax({
             type: 'GET',
             url: url,
             dataType: 'json',
             global: false,
             async: false,
             success: function(data) {
                 return data;
             }
         }).responseText);
        }
        */

        // Load at start of page
        update_network_speed();
        update_ping();
        get_server_ip();
        get_client_ip();
        get_system_info();
        update_storage_paths();

        // Refresh every 30 seconds
        var refreshId = setInterval(function()
        {
            get_system_info();
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
            update_storage_paths();
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
