/*
* switch-house-lock
* garage-doors-1
*
* switch-light-1 - 5 :Interior
* switch-light-6 - 9 :Exterior
*  switch-light-6 : sonoff2
*  switch-light-7 : sonoff1
*  switch-light-8 : sonoff-valve
*
* wash-machine
* home-fridge
* tv-lcd
*
* switch-camera-1
* switch-camera-2
*
* */


var api;
!function (a) {
    "use strict";
    $.ajaxSetup({
        headers: { 'Authorization': 'Bearer hWd3uNMVpjaRAbPs9Nt3' }
    });
    var b;
    b = {
        getStatus: function () {
            console.log('api begin call status');
            $.get("/api/v1.0/status", function(data, status){
                if(data){
                    data = JSON.parse(data);
                    var d = JSON.parse(localStorage.getItem("switchValues")) || {};
                    if(d['switch-light-6'] != (data[1] == 'on')){
                        iot.switchSingle('switch-light-6', (data[1] == 'on'));
                    }
                    if(d['switch-light-7'] != (data[0] == 'on')){
                        iot.switchSingle('switch-light-7', (data[0] == 'on'));
                    }
                    if(d['switch-light-8'] != (data[2] == 'on')){
                        iot.switchSingle('switch-light-8', (data[2] == 'on'));
                    }
                }
            });
        },
        switchDevice: function (id, status) {
            console.log('Api begin post status');
            $.post("/api/v1.0/" + api.convertDevId(id), function(data){
                if(data){
                    // var d = JSON.parse(localStorage.getItem("switchValues")) || {};
                    iot.switchSingle(id, data == 'on')
                }
            });
        },
        convertDevId: function (id) {
            switch (id) {
                //Exterior
                case 'switch-light-6':
                    return 'sonoff2';
                case 'switch-light-7':
                    return 'sonoff1';
                case 'switch-light-8':
                    return 'sonoff-valve';
                //Interior
                case 'switch-light-1':
                case 'switch-light-2':
                case 'switch-light-3':
                case 'switch-light-4':
                case 'switch-light-5':
                default:
                    return '';
            }
        },
        revertId: function (devId) {
            switch (devId) {
                //Exterior
                case 'sonoff2':
                    return 'switch-light-6';
                case 'sonoff1':
                    return 'switch-light-7';
                case 'sonoff-valve':
                    return 'switch-light-8';
                //Interior
                // case 'switch-light-1':
                // case 'switch-light-2':
                // case 'switch-light-3':
                // case 'switch-light-4':
                // case 'switch-light-5':
                default:
                    return '';
            }
        }
    }, window.api = b
}(this.jQuery);