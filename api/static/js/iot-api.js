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
                    var ja = JSON.parse(data);
                    ja.forEach(function(obj) {
                        iot.switchSingle(api.revertId(obj.devId), Boolean(obj.status));
                    });

                }
            });
        },
        switchDevice: function (id, status) {
            var action = (status) ? 1 : 0;
            $.ajax({
                url: '/api/v1.0/' + api.convertDevId(id),
                data: JSON.stringify({'status': action}),
                contentType: "application/json",
                type: 'POST',
                dataType:"json",
                success: function(data) {
                    iot.switchSingle(id, Boolean(data.status));
                },
                error: function (error) {
                    alert('Cannot do action!')
                    location.reload();
                }
            });
        },
        switchGroup: function (target, status) {
            var action = (status) ? 1 : 0;
            $.each( api.convertDevId(target), function(index, value ) {
                $.ajax({
                    url: '/api/v1.0/' + value,
                    data: JSON.stringify({'status': action}),
                    contentType: "application/json",
                    type: 'POST',
                    dataType:"json",
                    success: function(data) {
                        iot.switchSingle(api.revertId(data.devId), Boolean(data.status));
                    },
                    error: function (error) {
                        alert('Cannot do action!')
                        location.reload();
                    }
                });
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
                case 'switch-ex-lights':
                    return ['sonoff1','sonoff2','sonoff-valve']
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
        },
        loadTimerDevice: function () {
            console.log('api begin call get timer for devices');
            $.get("/api/v1.0/timer", function(data, status){
                if(data){
                    var timers = JSON.parse(data);
                    $.each(timers, function(i, item) {
                        var _id = api.revertId(item.devId);
                        $('#spinner-'+ _id).hide();
                        $('#timer-'+ _id).append(
                        '<li class="list-group-item" data-id="'+item.devId+'" data-timer="'+item.timer+'">'+
                            '<p class="specs">'+item.timer+'</p>'+
                            '<p class="ml-auto mb-0">' +
                            '<select class="form-control custom-focus" id="timer-op-'+_id+'-'+item.timer+'">' +
                            '<option value="1">ON</option>' +
                            '<option value="0">OFF</option>' +
                            '<option value="2">TOGGLE</option>' +
                            '</select>' +
                            '</p>'+
                            '<p class="ml-auto mb-0 input-group clockpicker">'+
                            '<input type="text" class="form-control" value="'+item.at+'">'+
                            '<span class="input-group-addon">'+
                            '<span class="glyphicon glyphicon-time"></span>'+
                            '</span>'+
                            '</p>'+
                            '<p class="ml-auto mb-0"><button type="button" class="form-control btn btn-primary btn-sm" onclick="api.confirmModal(this)">X</button></p>' +
                        '</li>'
                        );
                        $('#timer-op-'+_id+'-'+item.timer).val(item.action);
                        $('#timer-op-'+_id+'-'+item.timer).change(function() {
                            var devId = $(this).parents('li').data("id")
                            var timer = $(this).parents('li').data("timer")
                            var action =  $( this ).val()
                            var at = $(this).parents('li').find('input').val();
                            var t = {"devId":devId, "timer": timer, "period" : "day", "at": at, "action": action}
                            api.updateTimerDevice(t);
                        });
                    });
                    api.initClockPicker();
                }
                api.showAddTimter();
            });
        },
        initClockPicker: function () {
            $('.clockpicker').clockpicker({
                placement: 'left',
                align: 'left',
                autoclose: true,
                donetext: 'Done',
                afterDone: function(input) {
                    var at = $(input).val()
                    var devId = $(input).parents('li').data("id")
                    var timer = $(input).parents('li').data("timer")
                    var action =  $(input).parents('li').find('select').val()
                    var t = {"devId":devId, "timer": timer, "period" : "day", "at": at, "action": action}
                    api.updateTimerDevice(t);
                }
            });
        },
        addTimerDevice: function (t) {
            var specs = $(t).parents('ul').find('li:last .specs');
            var timer = 1;
            if(specs != null && $.isNumeric( $(specs).text() )){
                timer = parseInt($(specs).text()) + 1;
            }
            var id = $(t).parents('ul').attr("id").replace('timer-','')
            var devId = api.convertDevId(id);

            $(t).parents('ul').append(
                '<li class="list-group-item" data-id="'+devId+'" data-timer="'+timer+'">'+
                '<p class="specs">'+timer+'</p>'+
                '<p class="ml-auto mb-0">' +
                '<select class="form-control custom-focus" id="timer-op-'+devId+'-'+timer+'">' +
                '<option value="1">ON</option>' +
                '<option value="0">OFF</option>' +
                '<option value="2">TOGGLE</option>' +
                '</select>' +
                '</p>'+
                '<p class="ml-auto mb-0 input-group clockpicker">'+
                '<input type="text" class="form-control" value="00:00">'+
                '<span class="input-group-addon">'+
                '<span class="glyphicon glyphicon-time"></span>'+
                '</span>'+
                '</p>'+
                '<p class="ml-auto mb-0">' +
                '<button type="button" class="form-control btn btn-primary btn-sm" onclick="api.confirmModal(this)">X</button>' +
                '</p>' +
                '</li>'
            );
            $(t).parents('ul').find('li:last .clockpicker').clockpicker({
                placement: 'left',
                align: 'left',
                autoclose: true,
                donetext: 'Done',
                afterDone: function(input) {
                    var at = $(input).val()
                    var devId = $(input).parents('li').data("id")
                    var timer = $(input).parents('li').data("timer")
                    var action =  $(input).parents('li').find('select').val()
                    var t = {"devId":devId, "timer": timer, "period" : "day", "at": at, "action": action}
                    api.updateTimerDevice(t);
                }
            });
            $('#timer-op-'+devId+'-'+timer).change(function() {
                var devId = $(this).parents('li').data("id")
                var timer = $(this).parents('li').data("timer")
                var action =  $( this ).val()
                var at = $(this).parents('li').find('input').val();
                var t = {"devId":devId, "timer": timer, "period" : "day", "at": at, "action": action}
                api.updateTimerDevice(t);
            });
        },
        updateTimerDevice: function (t) {
            if(t.devId != '' && t.timer > 0 && t.at != '' && t.action != ''){
                $.ajax({
                    url: '/api/v1.0/timer/'+t.devId+'/'+t.timer,
                    data: JSON.stringify({
                        "period": "day",
                        "at": t.at,
                        "action": t.action
                    }),
                    contentType: "application/json",
                    type: 'POST',
                    success: function(data) {
                        console.log(data);
                    },
                    error: function (error) {
                        alert('Cannot add timer!')
                        location.reload();
                    }
                });
            }
        },
        deleteTimerDevice: function (d, t, l) {
            $.ajax({
                url: '/api/v1.0/timer/'+d+'/'+t,
                type: 'DELETE',
                success: function(result) {
                    $(l).parents('li').remove();
                }
            });
        },
        showAddTimter: function () {
            $('[id^=spinner-switch-light-]').each(function() {
                $(this).next().prepend('<li class="list-group-item">' +
                    '<p class="specs">Timer</p>' +
                    '<p class="ml-auto mb-0"><button type="button" class="form-control btn btn-primary btn-sm" onclick="api.addTimerDevice(this)">+</button></p>' +
                    '</li>')
                if(!$(this).is(":hidden")){
                    $(this).hide();
                }
            })

        },
        confirmModal: function (t) {
            var devId = $(t).parents('li').data("id");
            var timer = $(t).parents('li').data("timer");
            a("#confModal").modal("show"), a("#confModal .timer").text(timer);
            a("#confModal .timer-delete").bind( "click", function() {
                api.deleteTimerDevice(devId,timer, t)
                $(this).unbind( "click" );
                a("#confModal").modal("hide")
            });
            a("#confModal .timer-close").bind( "click", function() {
                a("#confModal .timer-delete").unbind( "click" );
            });
        }
    }, window.api = b
}(this.jQuery);