mx.GalleryAnimation = (function( ret ) {
    ret.TYPE_INSTANT = "instant";
    ret.TYPE_SMOOTH = "smooth";

    var requestId = null;
    var startPos = null;
    var diff = null;
    var duration = null;
    var startTime = null;
    var currentPos = null;

    var isHorizontal = null;

    ret.scrollTo = function(options)
    {
        if( options["behavior"] == "instant" )
        {
            mx.GalleryAnimation.stop();
            window.scrollTo(options);
        }
        else
        {
            isHorizontal = "left" in options;
            if( isHorizontal )
            {
                // scrollX is not 100% reliable during animations on mobile devices.
                startPos = currentPos == null ? window.scrollX : currentPos;
                diff = options["left"] - startPos;
                duration = Math.abs(diff) * 800 / window.innerWidth;
            }
            else
            {
                // scrollY is not 100% reliable during animations on mobile devices.
                startPos = currentPos == null ? window.scrollY : currentPos;
                diff = options["top"] - startPos;
                duration = Math.abs(diff) * 800 / window.innerHeight;
            }

            if( duration > 2000 ) duration = 2000;
            startTime = null;

            if( requestId != null ) return;

            const loop = function (currentTime) {
                if( requestId == null ) return;

                if (!startTime) startTime = currentTime;

                const time = currentTime - startTime;
                const percent = Math.min(time / duration, 1);
                // https://easings.net/de => easeOutCubic
                const animation = function (x) { return 1 - Math.pow(1 - x, 3); };

                currentPos = startPos + diff * animation(percent);
                if( isHorizontal ) window.scrollTo(currentPos, 0);
                else window.scrollTo(0, currentPos);

                // Continue moving
                if (time < duration) requestId = window.requestAnimationFrame(loop);
                else requestId = currentPos = null;
            };
            requestId = window.requestAnimationFrame(loop);
        }
    }

    ret.isScrolling = function()
    {
        return requestId != null;
    }

    ret.stop = function()
    {
        if( requestId == null ) return;

        window.cancelAnimationFrame(requestId);
        requestId = currentPos = null;
    }

    return ret;
})( mx.GalleryAnimation || {} );

mx.GallerySwipeHandler = (function( ret ) {
    var isMoving = false;
    var startClientX = 0;
    var startScrollX = 0;

    var tabticker = null;
    var trackerCurrentOffset = 0;
    var trackerLastOffset = 0;
    var trackerVelocity = 0;
    var trackerTimestamp = null;

    var swipeCallback = null;
    var swipeElement = null;

    function tabtracker()
    {
        var now = performance.now();
        var elapsed = now - trackerTimestamp;
        var delta = trackerCurrentOffset - trackerLastOffset;

        trackerLastOffset = trackerCurrentOffset;

        v = 1000 * delta / (1 + elapsed);
        trackerVelocity = 0.8 * v + 0.2 * trackerVelocity;

        trackerTimestamp = now;
    }

    function tapstart(e)
    {
        if( e.target.classList.contains("button") ) return;

        mx.GalleryAnimation.stop();

        isMoving = false;
        startClientX = e.detail.clientX;
        startScrollX = window.scrollX;

        trackerCurrentOffset = e.detail.clientX;
        trackerLastOffset = e.detail.clientX;
        trackerVelocity = 0;
        trackerTimestamp = performance.now();
        tabticker = setInterval(tabtracker, 100);

        swipeElement.addEventListener("tapmove",tapmove);
        swipeElement.addEventListener("tapend",tapend);
    }

    function tapmove(e)
    {
        isMoving = true;
        trackerCurrentOffset = e.detail.clientX;

        var diff = e.detail.clientX - startClientX;
        window.scrollTo( startScrollX - diff, 0 );
    }

    function tapend(e)
    {
        clearInterval(tabticker);

        swipeElement.removeEventListener("tapmove",tapmove);
        swipeElement.removeEventListener("tapend",tapend);

        if( !isMoving ) return;

        if( trackerVelocity == 0 ) tabtracker();
        swipeCallback(trackerVelocity);
    }

    ret.enable = function(element, callback)
    {
        swipeCallback = callback;
        swipeElement = element;

        element.addEventListener("tapstart",tapstart);
    }

    ret.disable = function()
    {
        swipeElement.removeEventListener("tapstart",tapstart);
    }

    return ret;
})( mx.GallerySwipeHandler || {} );

mx.Gallery = (function( ret ) {
    var isFullscreen = false;
    
    var activeItem = null;
    var activeSlot = null;
    var slotTooltipElement = null;

    var imageHeight = 0;
    var imageWidth = 0;
    var folder = null;
    
    var slotOverview = null;

    var gallery = null;
    var galleryPreviousButton = null;
    var galleryNextButton = null;
    var galleryStartPlayButton = null;
    var galleryStopPlayButton = null;
  
    var galleryRect = null;

    var containers = [];
    
    var containerObserver = null;
    var visibleContainer = [];

    var playTimer = null;
    var isPlaying = false;

    function buildContainer(element_data){
        var container = document.createElement("div");
        container.classList.add("container");
        container.dataset.index = element_data["index"];
        container.setAttribute("onclick", "mx.Gallery.openDetails(this)" );
        container.dataset.src = element_data["org"];
        container.dataset.small_src = element_data["small"];
        container.dataset.medium_src = element_data["medium"];
        container.dataset.formattedtime = element_data["time"];
        container.dataset.timeslot = element_data["slot"];

        var dummy = document.createElement("div");
        dummy.classList.add("dummy");
        container.appendChild(dummy);

        return container;

        gallery.appendChild(container);
    }

    function updateList()
    {
        var url = mx.Host.getBase() + 'index_update.php';

        var xhr = new XMLHttpRequest();
        xhr.open("POST", url );
        xhr.onreadystatechange = function() {
            if (this.readyState != 4) return;

            if( this.status == 200 )
            {
                var content = document.createElement("div");
                content.innerHTML = this.response;

                if( content.querySelector("#gallery") )
                {
                    var containerMap = {};
                    containers.forEach(function(container,index){ containerMap[container.dataset.src] = container; });

                    var container_data = JSON.parse(content.querySelector("#gallery").innerText);
                    var _nextContainer = containers[0];
                    Object.values(container_data).forEach(function(element_data,index)
                    {
                        if( typeof containerMap[element_data["org"]] == "undefined" )
                        {
                            var container = buildContainer(element_data);
                            if( _nextContainer ) gallery.insertBefore(container,_nextContainer);
                            else gallery.appendChild(container);

                            containerObserver.observe(container);
                        }
                        else
                        {
                            _nextContainer = containerMap[element_data["org"]].nextSibling;
                            containerMap[element_data["org"]].dataset.index = element_data["index"];
                            delete containerMap[element_data["org"]];
                        }
                    });

                    var _activeItem = activeItem;
                    Object.values(containerMap).forEach(function(container,index)
                    {
                        container.parentNode.removeChild(container);
                        if( container.dataset.src == activeItem.dataset.src ) _activeItem = null;
                    });

                    if( _activeItem == null ) _activeItem = containers[0]

                    // refresh containers
                    containers = gallery.querySelectorAll(".container");

                    slotOverview.innerHTML = content.querySelector("#slots").innerHTML;

                    // reset active states
                    activeItem = null;
                    activeSlot = null;
                    slotTooltipElement = null;

                    if( ( isFullscreen ? window.scrollX : window.scrollY ) == 0 ) setActiveItem(containers[0]);
                    else scrollToActiveItem(_activeItem,mx.GalleryAnimation.TYPE_INSTANT);
                }

                updateTimer = window.setTimeout(updateList,30000);
            }
            else
            {
                updateTimer = mx.Page.handleRequestError(this.status,url,updateList,60000);
            }
        };

        var data = {};
        data['count'] = containers.length;
        data['sub'] = folder;

        xhr.send(JSON.stringify(data));
    }

    function getOffset(element)
    {
        var offset = {left:0,top:0,height:element.offsetHeight, width:element.offsetWidth};
        while (element)
        {
            offset.left += element.offsetLeft;
            offset.top += element.offsetTop;
            offset.left -= element.scrollLeft;
            offset.top -= element.scrollTop;
            element = element.offsetParent;
        }
        offset.left -= window.pageXOffset;
        offset.top -= window.pageYOffset;
        
        return offset;
    }

    function getNextItem()
    {
        var index = parseInt(activeItem.dataset.index) - 1;
        return index >= 0 ? containers[index] : null;
    }

    function getPreviousItem()
    {
        var index = parseInt(activeItem.dataset.index) + 1;
        return index < containers.length ? containers[index] : null;
    }

    function positionSlotTooltip()
    {
        if( !slotTooltipElement.dataset.count )
        {
            mx.Tooltip.hide();
            return;
        }

        let text = slotTooltipElement.dataset.formattedtime + "<br>" + slotTooltipElement.dataset.count + " Bilder";
        mx.Tooltip.setText(text);

        var slotOverviewRect = slotOverview.getBoundingClientRect();
        var slotRect = slotTooltipElement.getBoundingClientRect();
        var tooltipRect = mx.Tooltip.getRootElementRect();
        var tooltipArrowRect = mx.Tooltip.getArrowElementRect();

        var pos = ( slotRect.left + slotRect.width / 2 - tooltipRect.width / 2 )
        if( pos < 2 )
        {
            pos = 2;
            var center = slotRect.left + slotRect.width / 2;
            arrowLeft = ( center - pos - tooltipArrowRect.width / 2 + 1) + "px";
        }
        else if( pos + tooltipRect.width > slotOverviewRect.width )
        {
            pos = slotOverviewRect.width - 2 - tooltipRect.width;
            var center = slotRect.left + slotRect.width / 2;
            arrowLeft = ( center - pos - tooltipArrowRect.width / 2 + 1) + "px";
        }
        else
        {
            arrowLeft = "calc(50% - " + (tooltipArrowRect.width / 2 - 1) + "px)";
        }

        mx.Tooltip.show(pos, 0, arrowLeft);
    }
    
    function setSlotTooltip(element)
    {
        if( element == slotTooltipElement ) return;
        
        if( slotTooltipElement != null ) slotTooltipElement.classList.remove("active");
        
        slotTooltipElement = element;
        slotTooltipElement.classList.add("active");
        
        positionSlotTooltip();
    }

    function slotHoverHandler(e)
    {
        var reference = e.target;
        if( !reference.classList ) return;

        if( reference.classList.contains("bar") ) reference = reference.parentNode;

        if( !reference.classList.contains("slot") )
        {
            if( activeSlot ) setSlotTooltip(activeSlot);
            return;
        }

        setSlotTooltip(reference);
    }
    
    function requiredImageSize()
    {
        return isFullscreen ? 2: 1;
    }

    function isImageLoaded(element)
    {
        return element.dataset.loaded >= requiredImageSize();
    }

    function loadImage(element,callback)
    {
        if( isImageLoaded(element) ) return;

        element.dataset.loaded = requiredImageSize();

        var img = element.querySelector("img");
        var isNew = !img;
        if( isNew ) img = document.createElement("img");

        if( typeof callback != "undefined" )
        {
            img.onload = function() { callback(true); };
            img.onerror = function() { callback(false); };
        }

        if( isFullscreen ) img.src = "./cache/" + folder + "/" + element.dataset.src;
        else img.src = "./cache/" + folder + "/" + element.dataset.medium_src;

        if( isNew )
        {
            element.appendChild(img);

            element.addEventListener("dragstart",function(e){ e.preventDefault(); });

            var srcLabel = document.createElement("span");
            srcLabel.innerHTML = element.dataset.src;
            element.appendChild(srcLabel);

            var timeLabel = document.createElement("span");
            timeLabel.innerHTML = element.dataset.formattedtime;
            element.appendChild(timeLabel);
        }
    }

    function delayedLoading(element)
    {
        if( isImageLoaded(element) ) return;

        var id = window.setTimeout(function(){ element.removeAttribute("data-timer"); loadImage(element); },100);
        element.dataset.timer = id;
    }

    function cancelLoading(element)
    {
        if( !element.dataset.timer ) return;

        window.clearTimeout(element.dataset.timer);
        element.removeAttribute("data-timer");
    }

    function scrollToActiveItem(item,behavior)
    {
        if( isFullscreen )
        {
            if( Math.round(window.scrollX) != item.offsetLeft ) mx.GalleryAnimation.scrollTo({ left: item.offsetLeft, behavior: behavior });
        }
        else
        {
            var targetPosition = item.offsetTop - gallery.offsetTop;
            if( Math.round(window.scrollY) != targetPosition ) mx.GalleryAnimation.scrollTo({ top: targetPosition, behavior: behavior });
        }
        
        setActiveItem(item);
    }
    
    function setActiveItem(item)
    {
        if( item != activeItem )
        {
            if( activeItem == null || activeItem.dataset.timeslot != item.dataset.timeslot )
            {
                if( activeItem != null ) activeSlot.classList.remove("active");
                activeSlot = slotOverview.querySelector(".slot[data-timeslot=\"" + item.dataset.timeslot + "\"]");
                activeSlot.classList.add("active");
                setSlotTooltip(activeSlot);
            }
            activeItem = item;
        }
        
        if( isFullscreen )
        {
            galleryStartPlayButton.style.display = activeItem.dataset.index == 0 || isPlaying ? "none" : "";
            galleryNextButton.style.display = activeItem.dataset.index == 0 ? "none" : "";
            galleryPreviousButton.style.display = activeItem.dataset.index == containers.length - 1 ? "none" : "";
        }
    }

    function getMostVisibleItem()
    {
        var scrollX = window.scrollX;
        var currentImageX = scrollX % activeItem.offsetWidth;
        var targetIndex = null;
        if( currentImageX / activeItem.offsetWidth > 0.5 )
        {
            targetIndex = (window.scrollX + activeItem.offsetWidth - currentImageX) / activeItem.offsetWidth;
        }
        else
        {
            targetIndex = (window.scrollX - currentImageX) / activeItem.offsetWidth;
        }

        return containers[targetIndex];
    }

    function delayedSlotPosition()
    {
        if( isFullscreen || visibleContainer.length == 0 ) return;

        if( mx.GalleryAnimation.isScrolling() ) return;

        var firstElement = visibleContainer[0];
        var minIndex = visibleContainer[0].dataset.index;
        visibleContainer.forEach(function(element,index){
            if( minIndex > element.dataset.index )
            {
                firstElement = element;
                minIndex = element.dataset.index
            }
        });

        setActiveItem(firstElement);
    }

    function initObserver()
    {
        var observerOptions = { rootMargin: ( ( galleryRect.top+window.scrollY ) * -1 ) + "px 0px 0px 0px" };

        containerObserver = new IntersectionObserver((entries, imgObserver) => {
            var activeItemUpdateNeeded = activeItem == null;

            entries.forEach((entry) => {
                if( entry.isIntersecting )
                {
                    activeItemUpdateNeeded = true;
                    delayedLoading(entry.target);
                    visibleContainer.push(entry.target);
                }
                else
                {
                    if( activeItem == entry.target ) activeItemUpdateNeeded = true;
                    cancelLoading(entry.target);
                    var index = visibleContainer.indexOf(entry.target)
                    if( index != -1 ) visibleContainer.splice(index, 1);
                }
            });

            if( activeItemUpdateNeeded ) delayedSlotPosition();
        },observerOptions);

        containers.forEach( function(container,index){ containerObserver.observe(container); });
    }

    function swipeHandler(velocity)
    {
        var item = null, direction = 0;

        if (velocity > 500 )
        {
            item = getNextItem();
            direction = -1;
        }
        else if( velocity < -500 )
        {
            item = getPreviousItem();
            direction = 1;
        }

        if( item != null )
        {
            scrollToActiveItem(item, mx.GalleryAnimation.TYPE_SMOOTH);

            item = direction == -1 ? getNextItem() : getPreviousItem();
            if( item != null ) delayedLoading(item);
        }
        else
        {
            scrollToActiveItem(getMostVisibleItem(),mx.GalleryAnimation.TYPE_SMOOTH);
        }
    }

    function playIteration()
    {
        if( isPlaying == false ) return;

        var item = getNextItem();
        if( item == null )
        {
            mx.Gallery.stopPlay();
            return;
        }
        scrollToActiveItem(item,mx.GalleryAnimation.TYPE_INSTANT);

        item = getNextItem();
        if( item == null )
        {
            mx.Gallery.stopPlay();
            return;
        }
        if( !isImageLoaded(item) )
        {
            var startTime = new Date().getTime();
            cancelLoading(item);
            loadImage(item,function(success)
            {
                var endTime = new Date().getTime();
                var diff = endTime - startTime;
                if( diff > 500 ) playIteration();
                else playTimer = window.setTimeout(playIteration,500-diff);
            });
        }
        else
        {
            playTimer = window.setTimeout(playIteration,500);
        }
    }

    function resizeHandler()
    {
        if( !activeItem ) return;

        scrollToActiveItem(activeItem,mx.GalleryAnimation.TYPE_INSTANT);
        positionSlotTooltip();
    }

    function keyHandler(e)
    {
        e.preventDefault();

        if( isPlaying ) mx.Gallery.stopPlay();

        if( e["key"] == "ArrowLeft" ) mx.Gallery.jumpToNextImage();
        else if( e["key"] == "ArrowRight" ) mx.Gallery.jumpToPreviousImage();
    }

    ret.openDetails = function(item)
    {
        if( isFullscreen ) return;
        isFullscreen = true;

        loadImage(item);
        var nextItem = getNextItem();
        if( nextItem != null ) delayedLoading(nextItem);
        var previousItem = getPreviousItem();
        if( previousItem != null ) delayedLoading(previousItem);

        mx.GallerySwipeHandler.enable(gallery, swipeHandler);
        window.addEventListener("keydown",keyHandler);

        var layer = gallery.querySelector("div.layer");
        var img = item.querySelector("img");

        var scrollbarSize = window.innerWidth - document.documentElement.clientWidth;

        var sourceImgRect = img.getBoundingClientRect();
        var galleryRect = gallery.getBoundingClientRect();
        var galleryTop = galleryRect.top + window.scrollY;

        var targetLayerRect = {top: galleryTop, left: 0, width: window.innerWidth, height: window.innerHeight - galleryTop - scrollbarSize };
        var targetImgRect = {top: 0, left: 0, width: 0, height: 0 };
        var imgRatio = sourceImgRect.height / sourceImgRect.width;

        var ratio = targetLayerRect.width / sourceImgRect.width;
        if( sourceImgRect.height * ratio > targetLayerRect.height ) ratio = targetLayerRect.height / sourceImgRect.height;
        targetImgRect.height = sourceImgRect.height * ratio;
        targetImgRect.width = sourceImgRect.width * ratio;
        //if( targetImgRect.height > imageHeight ) targetImgRect.height = imageHeight;
        //if( targetImgRect.width > imageWidth ) targetImgRect.width = imageWidth;
        targetImgRect.top = targetLayerRect.top + ( targetLayerRect.height - targetImgRect.height ) / 2 - 1;
        targetImgRect.left = targetLayerRect.left + ( targetLayerRect.width - targetImgRect.width ) / 2 - 1;

        layer.style.cssText = "display: block; top: " + targetLayerRect.top + "px; left: " + targetLayerRect.left + "px; width: " + targetLayerRect.width + "px; height: " + targetLayerRect.height + "px";
        img.style.cssText = "position: fixed; z-index: 50; top: " + sourceImgRect.top + "px; left: " + sourceImgRect.left + "px; width: " + sourceImgRect.width + "px; height: " + sourceImgRect.height + "px;";

        // force refresh
        img.offsetHeight;

        window.setTimeout(function() { layer.style.opacity = "1.0"; }, 150);

        img.style.cssText = "position: fixed; z-index: 50; transition: all 0.3s; top: " + targetImgRect.top + "px; left: " + targetImgRect.left + "px; width: " + targetImgRect.width + "px; height: " + targetImgRect.height + "px;";

        window.setTimeout(function(){
            gallery.classList.add("fullscreen");

            layer.style.cssText = "";
            img.style.cssText = "";

            scrollToActiveItem(item,mx.GalleryAnimation.TYPE_INSTANT);
            positionSlotTooltip();
        },300);
    }

    ret.closeDetails = function()
    {
        if( !isFullscreen ) return;
        isFullscreen = false;

        mx.GallerySwipeHandler.disable();
        window.removeEventListener("keydown",keyHandler);

        var layer = gallery.querySelector("div.layer");
        var img = activeItem.querySelector("img");

        var sourceImgRect = getOffset(img);
        sourceImgRect.left = img.offsetLeft;
        var sourceLayerRect = getOffset(activeItem);
        sourceLayerRect.left = 0;

        gallery.classList.remove("fullscreen");

        scrollToActiveItem(activeItem,mx.GalleryAnimation.TYPE_INSTANT);

        var targetImgRect = getOffset(img);

        layer.style.cssText = "display: block; top: " + sourceLayerRect.top + "px; left: " + sourceLayerRect.left + "px; width: " + sourceLayerRect.width + "px; height: " + sourceLayerRect.height + "px; opacity: 1.0";
        img.style.cssText = "position: fixed; z-index: 50; top: " + sourceImgRect.top + "px; left: " + sourceImgRect.left + "px; width: " + sourceImgRect.width + "px; height: " + sourceImgRect.height + "px;";

        // force refresh
        img.offsetHeight;

        layer.style.opacity = "";
        img.style.cssText = "position: fixed; z-index: 50; transition: all 0.3s; top: " + targetImgRect.top + "px; left: " + targetImgRect.left + "px; width: " + targetImgRect.width + "px; height: " + targetImgRect.height + "px;";

        window.setTimeout(function(){
            layer.style.display = "";
            img.style.cssText = "";

            positionSlotTooltip();
        },300);
    }

    ret.stopPlay = function(e)
    {
        if( e && e.target.classList.contains("button") && e.target.classList.contains("stop") && e.type == 'tapstart' ) return;

        isPlaying = false;

        if( playTimer != null )
        {
            window.clearTimeout(playTimer);
            playTimer = null;
        }

        galleryStartPlayButton.style.display = activeItem.dataset.index == 0 ? "none" : "";
        galleryStopPlayButton.style.display = "";

        document.removeEventListener("tapstart",mx.Gallery.stopPlay);

    }

    ret.startPlay = function(e)
    {
        isPlaying = true;

        galleryStartPlayButton.style.display = "none";
        galleryStopPlayButton.style.display = "inline";

        document.addEventListener("tapstart",mx.Gallery.stopPlay);

        playIteration();
    }

    ret.jumpToSlot = function(timeslot) {
        var firstItemInSlot = gallery.querySelector("div.container[data-timeslot='" + timeslot + "']");
        scrollToActiveItem(firstItemInSlot,mx.GalleryAnimation.TYPE_SMOOTH);
    }

    ret.jumpToPreviousImage = function()
    {
        var item = getPreviousItem();
        if( item == null ) return;
        scrollToActiveItem(item,mx.GalleryAnimation.TYPE_SMOOTH);
    }

    ret.jumpToNextImage = function()
    {
        var item = getNextItem();
        if( item == null ) return;
        scrollToActiveItem(item,mx.GalleryAnimation.TYPE_SMOOTH);
    }

    ret.init = function(_imageHeight,_imageWidth,_folder)
    {
        imageHeight = _imageHeight;
        imageWidth = _imageWidth;
        folder = _folder;
        
        slotOverview = document.querySelector(".slots");

        gallery = document.querySelector("#gallery");
        galleryPreviousButton = gallery.querySelector(".button.previous");
        galleryNextButton = gallery.querySelector(".button.next");
        galleryStartPlayButton = gallery.querySelector(".button.start");
        galleryStopPlayButton = gallery.querySelector(".button.stop");

        var data = JSON.parse(gallery.querySelector(".data").innerText);
        data.forEach(function(element_data){ var container = buildContainer(element_data); gallery.appendChild(container); });

        var style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = 'div.dummy { margin-top: ' + (imageHeight*100/imageWidth) + '%; }';
        document.getElementsByTagName('head')[0].appendChild(style);
        
        galleryRect = gallery.getBoundingClientRect();
        containers = gallery.querySelectorAll(".container");
        
        initObserver();

        window.addEventListener('resize', resizeHandler);
        document.addEventListener('mousemove', slotHoverHandler, {passive: true});
        
        mx.Swipe.init();
    
        updateTimer = window.setTimeout(updateList,30000);
    }
    
    return ret;
})( mx.Gallery || {} );
