<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="<?php echo Ressources::getCSSPath('/shared/'); ?>" rel="stylesheet">
<link href="<?php echo Ressources::getCSSPath('/system_service/'); ?>" rel="stylesheet">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [], Translations: [] };</script>
<script src="<?php echo Ressources::getJSPath('/shared/'); ?>"></script>
<script src="<?php echo Ressources::getJSPath('/system_service/'); ?>"></script>
<script src="<?php echo Ressources::getComponentPath('/system_service/'); ?>"></script>
<script>
mx.UNCore = (function( ret ) {
    var groups = {};    
    var devices = {};    
    var stats = {};    
    var root_device_mac = null;
    
    var nodes = {};
    
    var rootNode = null;
    
    var isTable = false;

    function getGroup(gid)
    {
        return groups[gid];
    }
    
    function getDeviceStat(device)
    {
        return stats.hasOwnProperty(device["mac"]) ? stats[device["mac"]] : null;
    }

    function getInterfaceStat(device)
    {
        if( device["connection"] )
        {
            key = device["connection"]["target_mac"] + ":" + device["connection"]["target_interface"];
            if( stats.hasOwnProperty(key) ) return stats[key];
        }
        return null;
    }

    function isOnline(device)
    {
        if( device.type == 'hub' )
        {
            let all_children_online = true;
            for(let child_device of device.connected_from) 
            {
                let child_device_stat = getDeviceStat(child_device);
                if( !child_device_stat || child_device_stat.offline_since != null )
                {
                    all_children_online = false;
                    break;
                }
            }
            return all_children_online;
        }

        let device_stat = getDeviceStat(device);
        return device_stat && device_stat.offline_since == null;
    }

    function initNode(device)
    {
        let node = {};
        node["name"] = device["mac"];
        node["device"] = device;
        node["children"] = [];

        nodes[device["mac"]] = node;

        return node;
    }
    
    function initChildren(parentNode, devices, stats)
    {
        let connectedDevices = Object.values(devices).filter(data => data["connection"] && parentNode["device"]["mac"] == data["connection"]["target_mac"]);
        
        for( i in connectedDevices)
        {
            if( connectedDevices[i]["mac"] in nodes )
            {
                continue;
            }
          
            childNode = initNode(connectedDevices[i], stats);
            parentNode["children"].push(childNode);

            if( childNode["device"]["connected_from"].length > 0 )
            {
                initChildren(childNode, devices, stats);
            }
        }
    }
    
    function buildStructure()
    {
        nodes = {};

        Object.values(devices).forEach(function(device)
        {
            device["connected_from"] = [];
        });

        Object.values(devices).forEach(function(device)
        {
            if( !device["connection"] || !devices[device["connection"]["target_mac"]] ) return;
            
            devices[device["connection"]["target_mac"]]["connected_from"].push(device);
        });

        let rootDevices = Object.values(devices).filter(data => root_device_mac == data["mac"] );
        if( rootDevices.length > 0 )
        {
            rootNode = initNode(rootDevices[0], stats);
        
            if( rootNode["device"]["connected_from"].length > 0 )
            {
                initChildren(rootNode, devices, stats);
            }
        }
        else
        {
            rootNode = null;
        }
    }

    function processData(data)
    {
        //console.log(rootNode);

        if( data.hasOwnProperty("root") ) root_device_mac = data["root"];
        
        // **** PROCESS DEVICES ****
        let replacesNodes = data["devices"]["replace"];
        
        let now = new Date().getTime();
        let _devices = {}
        if( replacesNodes ) devices = {}
        data["devices"]["values"].forEach(function(device)
        {
            device["update"] = now;
            devices[device["mac"]] = device;
            _devices[device["mac"]] = device;
        });
        
        // **** SORT DEVICES ****
        if( data["devices"]["values"].length > 0 )
        {
            _devices = Object.values(devices).sort(function(a, b)
            {
                if( a.ip == null ) return -1;
                if( b.ip == null ) return 1;
                
                if( a.ip.length > b.ip.length ) return 1;
                if( a.ip.length < b.ip.length ) return -1;
                
                return a.ip > b.ip;
            });
            
            devices = {}
            _devices.forEach(function(device)
            {
                devices[device["mac"]] = device;
            });
        }
        
        // **** BUILD REPLACED STRUCTURE ****
        if( replacesNodes || rootNode == null ) 
        {
            if( rootNode == null ) mx.Error.confirmSuccess();
            
            buildStructure();
            
            _devices = devices;
            replacesNodes = true;
        }
        // **** UPDATE STRUCTURE ****
        else
        {
            Object.values(nodes).forEach(function(node)
            {
                node["device"] = devices[node["device"]["mac"]];
            });
        }
        
        // **** PROCESS GROUPS ****
        data["groups"]["added"].forEach(function(group)
        {
            group["update"] = now;
            groups[group["gid"]] = group;
        });
        data["groups"]["modified"].forEach(function(group)
        {
            group["update"] = now;
            groups[group["gid"]] = group;
        });
        data["groups"]["deleted"].forEach(function(group)
        {
            delete groups[group["gid"]];
        });

        // **** PROCESS STATS ****
        data["stats"]["added"].forEach(function(stat)
        {
            stat["update"] = now;
            key = stat["interface"] ? stat["mac"]+":"+stat["interface"] : stat["mac"];
            stats[key] = stat;
        });
        data["stats"]["modified"].forEach(function(stat)
        {
            stat["update"] = now;
            key = stat["interface"] ? stat["mac"]+":"+stat["interface"] : stat["mac"];
            stats[key] = stat;
        });
        data["stats"]["deleted"].forEach(function(stat)
        {
            key = stat["interface"] ? stat["mac"]+":"+stat["interface"] : stat["mac"];
            delete stats[key];
        });
        
        Object.values(devices).forEach(function(device)
        {
            device["isOnline"] = isOnline(device);
            device["deviceStat"] = getDeviceStat(device);
            device["interfaceStat"] = getInterfaceStat(device);
            
            if( device["deviceStat"] && device["deviceStat"]["update"] > device["update"] ) device["update"] = device["deviceStat"]["update"];
            if( device["interfaceStat"] && device["interfaceStat"]["update"] > device["update"] ) device["update"] = device["interfaceStat"]["update"];
            
            _groups = [];
            if( device["connection"] )
            {
                device["connection"]["details"].forEach(function(details)
                {
                    if( details["gid"] ) _groups.push(getGroup(details["gid"]));
                });
            }
            device["groups"] = _groups;
        });
        
        //console.log(stats);
        
        if( rootNode == null )
        {
            mx.Error.handleError( mx.I18N.get("Network analysis is in progress")  );
        }
        else
        {
            if( isTable)
            {
                mx.NetworkTable.draw( replacesNodes ? rootNode : null, groups, stats);
            }
            else
            {
                mx.NetworkStructure.draw( replacesNodes ? rootNode : null, groups, stats);
            }
        }
    }
        
    ret.init = function()
    { 
        mx.I18N.process(document);
        
        //refreshDaemonState(null, function(state){});
        
        function handleErrors()
        {
            mx.Error.handleError( mx.I18N.get( "Service is currently not available") );
        }
        const socket = io("/", {path: '/system_service/api/socket.io' });
        socket.on('connect', function() {
            mx.Error.confirmSuccess();
            socket.emit('call', "network_data");
        });
        socket.on('network_data', function(data) {
            processData(data);
        });
        socket.on('connect_error', err => handleErrors(err))
        socket.on('connect_failed', err => handleErrors(err))
        socket.on('disconnect', err => handleErrors(err))
        
        mx.$("#networkToolbar .networkDisplay.button").addEventListener("click",function()
        {
            isTable = !isTable;

            if( isTable )
            {
                mx.$("#networkToolbar .networkDisplay.button span").className = "icon-flow-tree";
                mx.NetworkTable.draw( rootNode, groups, stats);
            }
            else
            {
                mx.$("#networkToolbar .networkDisplay.button span").className = "icon-table";
                mx.NetworkStructure.draw( rootNode, groups, stats);
            }
        });
        
        mx.$("#networkToolbar .networkSearch.button").addEventListener("click",function()
        {
            let element = mx.$("#networkToolbar .networkSearchInput");
            element.classList.toggle("active");
            
            /*dialog = mx.Dialog.init({
                title: "Not implement",
                body: "Needs still time to implement",
                buttons: [
                    { "text": "OK" },
                ],
                destroy: true
            });
            dialog.open();*/
        });
    }
    return ret;
})( mx.UNCore || {} );

mx.OnDocReady.push( mx.UNCore.init );
</script>
</head>
<body class="inline">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("", mx.I18N.get("Network visualizer")); } );</script>
<div class="contentLayer error"></div>
<svg id="networkStructure"></svg>
<div id="networkList"></div>
<div id="networkToolbar"><div class="networkSearchInput"><input></div><div class="networkSearch form button"><span class="icon-search-1"></span></div><div class="networkDisplay form button"><span class="icon-table"></span></div></div>
</body>
</html>
