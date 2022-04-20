mx.D3 = (function( ret ) 
{
    let width = 1000;//bodyRect.width;
    let height = 1000;//bodyRect.height;
    
    //let boxMargin = 3;
    let boxPadding = 3;
    let boxWidth = 150;
    let boxHeight = 0;

    let bodyRect = {};
    let bodyWidth = null;
    let bodyHeight = null;

    let link = null;
    let node = null;
    
    let d3root = null;
    
    function initNode(device, stats, processedNodes)
    {
        processedNodes[device["mac"]] = true;

        let node = {};
        node["name"] = device["mac"];
        node["device"] = device;
        node["children"] = [];

        node["stat"] = stats[device["mac"]] ? stats[device["mac"]] : null;

        return node;
    }
    
    function initChildren(rootNode, devices, stats, processedNodes)
    {
        let connectedDevices = devices.filter(data => data["connection"] && rootNode["device"]["mac"] == data["connection"]["target_mac"]);
        
        for( i in connectedDevices)
        {
            if( connectedDevices[i]["mac"] in processedNodes )
            {
                continue;
            }
          
            childNode = initNode(connectedDevices[i], stats, processedNodes);
            rootNode["children"].push(childNode);

            if( childNode["device"]["connected_from"].length > 0 )
            {
                initChildren(childNode, devices, stats, processedNodes);
            }
        }
    }
    
    ret.drawCircles = function(devices, groups, stats, refresh_interval)
    {
        if( devices )
        {
            let processedNodes = {};
            let rootNode = null;
            
            device_uid_map = {}
            devices.forEach(function(device)
            {
                device["connected_from"] = [];
                device_uid_map[device["mac"]] = device;
            });

            devices.forEach(function(device)
            {
                if( !device["connection"] ) return;
                
                device_uid_map[device["connection"]["target_mac"]]["connected_from"].push(device["mac"]);
            });

            let endCount = devices.filter(data => data["connected_from"].length == 0 ).length;
            
            let rootDevices = devices.filter(data => !data["connection"] || data["connection"]["target_mac"] == data["mac"] );
            if( rootDevices.length == 1 )
            {
                rootNode = initNode(rootDevices[0], stats, processedNodes);
            
                if( rootNode["device"]["connected_from"].length > 0 )
                {
                    initChildren(rootNode, devices, stats, processedNodes);
                }
            }
            else
            {
                rootNode = {"uid": "dummy", "name": "root", "children": [], "device": {"is_online": false, "name": "0.0.0.0/24", "type": "placeholder" } }
                rootDevices.forEach(function(rootDevice)
                {
                    let _rootNode = initNode(rootDevice, stats, processedNodes);
                    rootNode["children"].push(_rootNode);

                    if( _rootNode["device"]["connected_from"].length > 0 )
                    {
                        initChildren(_rootNode, devices, stats, processedNodes);
                    }
                });
            }
            
            const width = 400;
            const height = 400;
            
            d3root = d3.hierarchy(rootNode);

            initTree(d3root, endCount, groups);
        }
        else
        {            
            d3root.descendants().forEach(function(_data)
            {
                let mac = _data["data"]["device"]["mac"];
                if(mac in stats) _data["data"]["stat"] = stats[mac];
            });

            redrawTraffic();
        }
    }
    
    ret.init = function(devices, groups, traffic)
    {
    }
    
    function initTree(root, endCount, groups)
    {
        bodyRect = document.body.getBoundingClientRect();
        bodyWidth = bodyRect.width;
        bodyHeight = bodyRect.height;

        // Compute the layout.
        const dx = ( height / endCount ) - ( 2 * boxPadding ) ;
        const dy = width / (root.height + 1);
        d3.tree().nodeSize([dx + 2, dy])(root);
        //d3.tree().size([300, 200])(root);
        
        boxHeight = dx;
        
        //console.log(boxHeight);

        // Center the tree.
        let x0 = Infinity;
        let x1 = -x0;
        root.each(d => {
            if (d.x > x1) x1 = d.x;
            if (d.x < x0) x0 = d.x;
        });
            
        // Compute the default height.
        if (height === undefined) height = x1 - x0 + dx * 2;

        const svg = d3.selectAll("#network")
            //.attr("viewBox", [-dy / 2 + ( dy / 3 ), x0 - dx, width, width])
            .attr("viewBox", [0, 0, width, width])
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("font-family", "sans-serif");
        
        svg.selectAll("g").remove()
        
        link = svg.append("g")
                .classed("links", true)
            .selectAll("path")
                .data(root.links())
            .join("path")
                .attr("d", linkGenerator);
                
        //var tooltip = d3.select("#tooltip");
                        
        node = svg.append("g")
            .classed("nodes", true)
            .selectAll("a")
            .data(root.descendants())
            .join("a")
        //      .attr("xlink:href", link == null ? null : d => link(d.data, d))
        //      .attr("target", link == null ? null : linkTarget)
            .attr("transform", d => `translate(${d.y},${d.x})`)
            .attr("id", function(d) { return d.data.uid; })
            .on("mouseenter", function(e, d){ 
                let device = d.data.device
                if( device && device.type != "placeholder" )
                {
                        let stat = d.data.stat

                        let html = "<div>";
                        if( device.ip ) html += "<div><div>IP:</div><div>" + device.ip + "</div></div>";
                        if( device.dns ) html += "<div><div>DNS:</div><div>" + device.dns + "</div></div>";
                        if( device.mac ) html += "<div><div>MAC:</div><div>" + device.mac + "</div></div>";
                        
                        if( stat )
                        {
                            let dateTimeMsg = "";
                            
                            if( !stat["offline_since"] )
                            {
                                dateTimeMsg = "Online";
                            }
                            else
                            {
                                let lastSeenTimestamp = Date.parse(stat["offline_since"]);
                                let lastSeenDatetime = new Date(lastSeenTimestamp)
                                
                                dateTimeMsg = lastSeenDatetime.toLocaleTimeString();
                                if( ( ( new Date().getTime() - lastSeenTimestamp ) / 1000 ) > 60 * 60 * 12 )
                                {
                                    dateTimeMsg = lastSeenDatetime.toLocaleDateString() + " " + dateTimeMsg
                                }
                                
                                dateTimeMsg = "Offline since " + dateTimeMsg;
                            }
                            
                            html += "<div><div>Status:</div><div>" + dateTimeMsg + "</div></div>";
                        }
                        if( device.info ) html += "<div><div>Info:</div><div>" + device.info + "</div></div>";
                        html += "<div><div>Type:</div><div>" + device.type + "</div></div>";
                        if( device.connection && device.connection["vlans"] ) html += "<div><div>VLAN:</div><div>" + device.connection["vlans"] + "</div></div>";
                        
                        if( device.connection["target_interface"] && device.connection["type"] != "wifi" ) html += "<div><div>Port:</div><div>" + device.connection["target_interface"] + "</div></div>";
                        
                        html += showRows(device.details,"Details","rows");
                        html += showRows(device.services,"Services","rows");
                        //html += showRows(device.ports,"Ports","rows");
                        
                        device.gids.forEach(function(gid){
                            let group = groups.filter(group => group["gid"] == gid );
                            html += showRows(group[0]["details"],group[0]["type"],"rows");
                        });
                        
                        if( stat )
                        {
                            let inSpeed = stat["speed"]["in"];
                            let outSpeed = stat["speed"]["out"];
                            
                            let duplex = "";
                            if( "duplex" in stat["details"] )
                            {
                                duplex += " - " + ( stat["details"]["duplex"] == "full" ? "FullDuplex" : "HalfDuplex" );
                            }
                            
                            html += "<div><div>Speed:</div><div>" + formatSpeed(inSpeed) + (inSpeed == outSpeed ? '' : ' RX / ' + formatSpeed(outSpeed) + " TX" ) + duplex + "</div></div>";

                            Object.entries(stat["details"]).forEach(function([key, value])
                            {
                                if( key == "duplex" ) return;
                                
                                if( key == "signal" ) value += " db";
                                html += "<div><div>" + capitalizeFirstLetter(key) + ":</div><div>" + value + "</div></div>";
                            });
                            //html += showRows(stat["traffic"],"Traffic","rows" );
                        }

                        html += "</div>"
                        
                        mx.Tooltip.setText(html);
                }
                else
                {
                    mx.Tooltip.hide();
                }
                
                link
                    .classed("online", false)
                    .classed("offline", false)
                    .filter(l => l.source.data === d.data || l.target.data === d.data)
                    .classed("online", d.data.stat && d.data.stat.offline_since == null)
                    .classed("offline", !d.data.stat || d.data.stat.offline_since != null);
            })
            .on("mousemove", function(e, d){
                let device = d.data.device
                if( device && device.type != "placeholder" )
                {
                    positionTooltip(this);
                }
            })
            .on("mouseleave", function(){
                link
                    .classed("online", false)
                    .classed("offline", false);
            })
            .on("click", function(e, d){
                let device = d.data.device
                if( device && device.type != "placeholder" )
                {
                    mx.Tooltip.toggle();
                    e.stopPropagation();
                }
            });
                
                
            svg.on("click", function(e, d){
                mx.Tooltip.hide();
            });

        node.append("rect")
            .attr("class", d => "container " + ( d.data["device"] ? d.data["device"]["type"] : "" ) )
            .attr("width", boxWidth)
            .attr("height", boxHeight);

        node.append("circle")
            .attr("class", d => ( d.data.stat && d.data.stat.offline_since == null ? "online" : "offline" ) )
            .attr("cx", 143)
            .attr("cy", 7)
            .attr("r", 3);

        //  if (title != null) node.append("title")
        //      .text(d => title(d.data, d));

        let font_size = boxHeight / 2.5
            
        node.append("text")
            .attr("dy", font_size * 1.1)
            .attr("x", "5")
            .attr("font-size", font_size)
        //      .attr("x", d => d.children ? -6 : 6)
        //      .attr("text-anchor", d => d.children ? "end" : "start")
            .text(d => d.data["device"]["ip"] ? d.data["device"]["ip"] : d.data["device"]["mac"] ).each( wrap );
        
        node.append("text")
            .attr("dy", font_size * 2 * 1.1)
            .attr("x", "5")
            .attr("font-size", font_size)
        //      .attr("x", d => d.children ? -6 : 6)
        //      .attr("text-anchor", "start")
            .text(d => d.data["device"]["dns"] ? d.data["device"]["dns"] : d.data["device"]["type"] ).each( wrap );

        let traffic_background = node.append("rect")
            .classed("traffic", true);

        let traffic_font_size = boxHeight / 4;
        let traffic_text = node.append("text")
            .classed("traffic", true)
            .text(d => getTrafficContent(d.data) )
            .attr("dy", traffic_font_size * 1.5)
            .attr("font-size", traffic_font_size)
            .each( setTrafficPosition );

        node.selectAll("rect.traffic").each( setTrafficBackground );
        
        let _svg = document.querySelector('svg');
        const { xMin, xMax, yMin, yMax } = [..._svg.children].reduce((acc, el) => {
            const { x, y, width, height } = el.getBBox();
            if (!acc.xMin || x < acc.xMin) acc.xMin = x;
            if (!acc.xMax || x + width > acc.xMax) acc.xMax = x + width;
            if (!acc.yMin || y < acc.yMin) acc.yMin = y;
            if (!acc.yMax || y + height > acc.yMax) acc.yMax = y + height;
            return acc;
        }, {});
        console.log(xMin, yMin, xMax - xMin, yMax - yMin);
        svg.attr("viewBox", [xMin - 10, yMin - 10, (xMax - xMin) + 20, (yMax - yMin) + 20])
    }
    
    function redrawTraffic() {
        let traffic_text = node.selectAll("text.traffic");
        traffic_text.text(function(d)
        {
            return getTrafficContent(d.data);
        })
        .each( setTrafficPosition );

        node.selectAll("rect.traffic").each( setTrafficBackground );

        let online_circle = node.selectAll("circle");
        online_circle.attr("class", d => ( d.data.stat && d.data.stat.offline_since == null ? "online" : "offline" ) );
    };
    
    function getTrafficContent(data)
    {
        if( !data["stat"] ) return "";
        
        let in_data = formatTraffic( data["stat"]["traffic"]["in_avg"]);
        let out_data = formatTraffic( data["stat"]["traffic"]["out_avg"]);
        
        let in_out_data = [];
        if( in_data != 0 ) in_out_data.push("⇩ " + in_data);
        if( out_data != 0 ) in_out_data.push("⇧ " + out_data);
        
        return in_out_data.length > 0 ? in_out_data.join(" • ") : "";
    }
    
    function formatTraffic(traffic)
    {
        if( traffic > 100000000 ) return Math.round( traffic / 1000000 ) + "MB/s";                  // >= 100MB
        
        if( traffic > 1000000 ) return ( Math.round( ( traffic / 1000000 ) * 10 ) / 10 ) + "MB/s";  // >= 1MB

        if( traffic > 100000 ) return Math.round( traffic / 1000 ) + "KB/s";                        // >= 100KB
        
        if( traffic > 1000 ) return ( Math.round( ( traffic / 1000 ) * 10 ) / 10 ) + "KB/s";        // >= 1KB
        
        if( traffic > 100 ) return ( Math.round(traffic / 100) / 10 ) + "KB/s";
        
        return 0;
    }

    function setTrafficPosition(d)
    {
        let self = d3.select(this);
        let textLength = self.node().getComputedTextLength() + 3;
        self.attr("x", textLength * -1);
    }

    function setTrafficBackground(d)
    {
        let self = d3.select(this);
        
        let rect = self.node().parentNode.querySelector("text.traffic").getBBox();
        self.attr("x", rect.x - 1);
        self.attr("y", rect.y - 1);
        self.attr("width", rect.width + 1);
        self.attr("height", rect.height + 1);
    }

    function linkGenerator(d) {
        let path = d3.linkHorizontal()
            .source(function (d) {
                return [ d.source.y + boxWidth - 30, (d.source.x + d.source.height / 2) + boxHeight / 2 ];
            })
            .target(function (d) {
                return [ d.target.y, (d.target.x + d.target.height / 2) + boxHeight / 2 ];
            });
                
        return path(d);
    }
        
    function positionTooltip(element)
    {
        element = element.querySelector("rect.container");
        
        let nodeRect = element.getBoundingClientRect();
        let tooltipRect = mx.Tooltip.getRootElementRect();

        let arrowOffset = 0;
        let arrowPosition = "right";
        
        let top = nodeRect.top;
        if( top + tooltipRect.height > bodyHeight ) 
        {
            top = bodyHeight - tooltipRect.height - 6;
            arrowOffset = tooltipRect.height - ( bodyHeight - ( nodeRect.top + nodeRect.height / 2 ) );
        }
        else
        {
            arrowOffset = nodeRect.height / 2;
        }

        let left = nodeRect.left - tooltipRect.width - 6;
        if( left < 0 )
        {
            left = nodeRect.left + nodeRect.width + 6;
            arrowPosition = "left";
        }

        mx.Tooltip.show(left, top, arrowOffset, arrowPosition );
        window.setTimeout(function(){ mx.Tooltip.getRootElement().style.opacity="1"; },0);
    }
    
    function wrap( d ) {
        var self = d3.select(this),
            textLength = self.node().getComputedTextLength(),
            text = self.text();
        while ( ( textLength > 145 )&& text.length > 0) {
            text = text.slice(0, -1);
            self.text(text + '...');
            textLength = self.node().getComputedTextLength();
        }
    }
        
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }
    
    function formatSpeed(speed)
    {
            if( speed >= 1000000000 ) return Math.round( speed * 10 / 1000000000 ) / 10 + " GBit";
            else if( speed >= 1000000 ) return Math.round( speed * 10 / 1000000 ) / 10 + " MBit";
            else if( speed >= 1000 ) return Math.round( speed * 10 / 1000 ) / 10 + " KBit";
            else return speed + " Bit";
    }
    
    function formatDetails(key, value)
    {
        if( ["ssid"].indexOf(key) != -1 )
        {
                key = key.toUpperCase()
        }
        else
        {
                key = capitalizeFirstLetter(key);
        }
        
        key = key.replace("_", " ");
        
        return [key, value]
    }

    function showRows(rows, name, cls)
    {
        let html = '';
        if( Object.entries(rows).length > 0)
        {
            html += "<div><div>" + capitalizeFirstLetter(name) + ":</div><div class='" + cls + "'><div>";
            Object.entries(rows).forEach(function([key, value])
            {
                [key, value] = formatDetails(key, value)
                
                if( value && typeof( value ) == "object" )
                {
                    Object.entries(value).forEach(function([key, value])
                    {
                        [key, value] = formatDetails(key, value)
                        
                        html += "<div><div>" + key + "</div><div>" + value + "</div></div>";
                    });
                }
                else
                {
                    html += "<div><div>" + key + "</div><div>" + value + "</div></div>";
                }
            });
            html += "</div></div></div>";
        }
        return html;
    }


    return ret;
})( mx.D3 || {} );