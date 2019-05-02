/*
* switch-house-lock
* garage-doors-1
*
* switch-light-1 - 5 :Interior
* switch-light-6 - 9 :Exterior
*  switch-light-6 : sonoff2
*  switch-pumper : sonoff1
*  switch-valve : sonoff-valve
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
var _IOTdevices_
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
            return id.replace('switch-','');
        },
        revertId: function (devId) {
            return 'switch-'+devId;
        },
        revertName: function (devId) {
            switch (devId) {
                //Exterior
                case 'sonoff2':
                    return 'Front doors';
                case 'sonoff1':
                    return 'Pumper';
                case 'sonoff-valve':
                    return 'Valve';
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
                            '<p class="specs">' + item.period.toUpperCase() +'</p>'+
                            '<p class="ml-auto mb-0">' +
                            '<select class="form-control timer-mode custom-focus" id="timer-op-'+_id+'-'+item.timer+'">' +
                            '<option value="1">ON</option>' +
                            '<option value="0">OFF</option>' +
                            '<option value="2">TOG</option>' +
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
                            var period = $(this).parents('ul').children(":first").find('select').val();
                            var t = {"devId":devId, "timer": timer, "period" : period, "at": at, "action": action}
                            api.updateTimerDevice(t);
                        });
                    });
                    api.initClockPicker();
                }
            });
            api.showAddTimter();
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
                    var period = $(input).parents('ul').children(":first").find('select').val();
                    var t = {"devId":devId, "timer": timer, "period" : period, "at": at, "action": action}
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
                '<select class="form-control timer-mode custom-focus" id="timer-op-'+devId+'-'+timer+'">' +
                '<option value="1">ON</option>' +
                '<option value="0">OFF</option>' +
                '<option value="2">TOG</option>' +
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
                    var period = $(input).parents('ul').children(":first").find('select').val()
                    var t = {"devId":devId, "timer": timer, "period" : period, "at": at, "action": action}
                    api.updateTimerDevice(t);
                }
            });
            $('#timer-op-'+devId+'-'+timer).change(function() {
                var devId = $(this).parents('li').data("id")
                var timer = $(this).parents('li').data("timer")
                var action =  $( this ).val()
                var at = $(this).parents('li').find('input').val();
                var period = $(this).parents('ul').children(":first").find('select').val();
                var t = {"devId":devId, "timer": timer, "period" : period, "at": at, "action": action}
                api.updateTimerDevice(t);
            });
        },
        updateTimerDevice: function (t) {
            if(t.devId != '' && t.timer > 0 && t.at != '' && t.action != '' && t.period != ''){
                $.ajax({
                    url: '/api/v1.0/timer/'+t.devId+'/'+t.timer,
                    data: JSON.stringify({
                        "period": t.period,
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
            $('[id^=spinner-]').each(function() {
                if(!$(this).is(":hidden")){
                    $(this).next().prepend('<li class="list-group-item">' +
                    '<p class="specs">Timer</p>' +
                    '<p class="ml-auto mb-0">' +
                    '<select class="form-control custom-focus">' +
                    '<option value="day">Daily</option>' +
                    '<option value="hour">Hourly</option>' +
                    '</select>' +
                    '</p>'+
                    '<p class="ml-auto mb-0"><button type="button" class="form-control btn btn-primary btn-sm" onclick="api.addTimerDevice(this)">+</button></p>' +
                    '</li>')
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
        },
        drawLightChart: function () {
            // Bar Chart initialization settings - Chartist.js
            $.get("/api/v1.0/chart", function(data, status){
                if(data){
                    var data01 = JSON.parse(data);
                    if (data01.series != null) {
                        data01.series.forEach(function(obj) {
                            obj.name = api.revertName(obj.name)
                        });
                    }
                    var options01 = {
                        axisY: {
                            labelInterpolationFnc: function(value) {
                                return value + 'm'
                            }
                        },
                        height: 240,
                        high: 500,
                        low: 0,
                        scaleMinSpace: 6,
                        onlyInteger: false,
                        referenceValue: 0,
                        seriesBarDistance: 8,
                        plugins: [
                            Chartist.plugins.legend({
                                position: 'bottom'
                            })
                        ]
                    };
                    var responsive_steps01 = [
                        // Show only every second label
                        ['screen and (max-width: 768px)', {
                            axisX: {
                                labelInterpolationFnc: function skipLabels(value, index, labels) {
                                    return index % 2 === 0 ? value : null;
                                }
                            }
                        }],
                        // Show only every fourth label
                        ['screen and (max-width: 480px)', {
                            axisX: {
                                labelInterpolationFnc: function skipLabels(value, index, labels) {
                                    return index % 4 === 0 ? value : null;
                                }
                            }
                        }]
                    ];
                    // Initialize a Bar chart in the container with the ID chart01
                    new Chartist.Bar('#chart01', data01, options01, responsive_steps01)
                        .on('draw', function(data001) {
                            if (data001.type === 'bar') {
                                data001.element.attr({
                                    style: 'stroke-width: 6px;'
                                });
                            }
                        });

                }
            });
        },
        drawHydroponicChart: function () {
            // Bar Chart initialization settings - Chartist.js
            $.get("/api/v1.0/hydro-chart", function(data, status){
                if(data){
                    var data01 = JSON.parse(data);
                    if (data01.series != null) {
                        data01.series.forEach(function(obj) {
                            obj.name = api.revertName(obj.name)
                        });
                    }
                    var options01 = {
                        axisY: {
                            labelInterpolationFnc: function(value) {
                                return value + 's'
                            }
                        },
                        axisX: {
                            labelInterpolationFnc: function(value, index) {
                                return index % 2 === 0 ? value : null;
                            }
                        },
                        height: 240,
                        high: 200,
                        low: 0,
                        // scaleMinSpace: 6,
                        // onlyInteger: false,
                        // referenceValue: 0,
                        // seriesBarDistance: 8,
                        plugins: [
                            Chartist.plugins.legend({
                                position: 'bottom'
                            })
                        ]
                    };
                    var responsive_steps01 = [
                        // Show only every second label
                        ['screen and (max-width: 768px)', {
                            axisX: {
                                labelInterpolationFnc: function skipLabels(value, index, labels) {
                                    return index % 2 === 0 ? value : null;
                                }
                            }
                        }],
                        // Show only every fourth label
                        ['screen and (max-width: 480px)', {
                            axisX: {
                                labelInterpolationFnc: function skipLabels(value, index, labels) {
                                    return index % 4 === 0 ? value : null;
                                }
                            }
                        }]
                    ];
                    // Initialize a Bar chart in the container with the ID chart01
                    new Chartist.Bar('#hydroponicChart', data01, options01, responsive_steps01)
                        .on('draw', function(data001) {
                            if (data001.type === 'bar') {
                                data001.element.attr({
                                    style: 'stroke-width: 6px;'
                                });
                            }
                        });

                }
            });
        },
        tableAction: function (action, data) {
            switch (action) {
                case 'add':
                    a("#updateModal").modal("show"); 
                    a("#modal-devId").val('');
                    a("#modal-name").val('');
                    a("#modal-status").val(1);
                    a("#modal-power").val(0);
                    a("#modal-vol").val(220);
                    a("#modal-cat").val('light');
                    a("#modal-icon").val('light');
                    a("#updateModal .device-update").text("Add");
                    break;
                case 'update':
                    if(data){
                        a("#updateModal").modal("show"); 
                        a("#modal-devId").val(data.devId);
                        a("#modal-name").val(data.name);
                        a("#modal-status").val(data.status);
                        a("#modal-power").val(data.power);
                        a("#modal-vol").val(data.vol);
                        a("#modal-cat").val(data.cat);
                        a("#modal-icon").val(data.icon);
                        a("#updateModal .device-update").text("Update");
                    }else{
                        alert('Please selete a row to update!')
                    }
                    break;
                case 'delete':
                    if(data){
                        var devId = data.devId;
                        a("#confModal").modal("show"), a("#confModal .timer").text(devId);
                        a("#confModal .timer-delete").bind( "click", function() {
                            api.deleteDevice(devId)
                            $(this).unbind( "click" );
                            a("#confModal").modal("hide")
                        });
                        a("#confModal .timer-close").bind( "click", function() {
                            a("#confModal .timer-delete").unbind( "click" );
                        });
                    }else{
                        alert('Please selete a row to delete!')
                    }
                    break;
                default:
                    return '';
            }
        },
        addOrUpdateDevice:function(){
            var dev = {};
            dev.devId = a("#modal-devId").val();
            dev.name = a("#modal-name").val();
            dev.status = a("#modal-status").val();
            dev.power = a("#modal-power").val();
            dev.vol = a("#modal-vol").val();
            dev.cat = a("#modal-cat").val();
            dev.icon = a("#modal-icon").val();
            api.addDevice(dev);
        },
        addDevice: function(dev){
            $.ajax({
                url: '/api/v1.0/device',
                data: JSON.stringify(dev),
                contentType: "application/json",
                type: 'POST',
                success: function(data) {
                    console.log(data);
                    var _row = iot_table.row('.selected').data();
                    if(typeof _row != "undefined"){
                        iot_table.row('.selected').data(JSON.parse(data)).draw();
                    }else{
                        iot_table.row.add(JSON.parse(data)).draw();
                    }
                    a("#updateModal").modal("hide")
                },
                error: function (error) {
                    alert('Cannot add device!')
                    a("#updateModal").modal("hide")
                }
            });
        },
        deleteDevice: function(devId){
            $.ajax({
                url: '/api/v1.0/device/'+devId,
                type: 'DELETE',
                success: function(data) {
                    iot_table.row('.selected').remove().draw( false );
                },
                error: function (error) {
                    alert('Cannot delete device!')
                }
            });
        }
    }, window.api = b
}(this.jQuery);