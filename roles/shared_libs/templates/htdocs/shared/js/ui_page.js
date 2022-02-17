mx.Page = (function( ret ) {
    function createRipple(event) {
        const button = event.currentTarget;
        
        const circle = document.createElement("span");
        const diameter = Math.max(button.clientWidth, button.clientHeight);
        const radius = diameter / 2;
        
        var offsets = mx.Core.getOffsets(button);
        
        circle.style.width = circle.style.height = diameter + "px";
        circle.style.left = ( event.clientX - (offsets.left + radius) ) + "px";
        circle.style.top = ( event.clientY - (offsets.top + radius) ) + "px";
        circle.classList.add("ripple"); 

        // cleanup for fast repeatedly clicks
        const ripple = button.getElementsByClassName("ripple")[0];
        if (ripple) ripple.remove();
           
        button.appendChild(circle);
        
        // autocleanup. Otherwise the ripple effect happens again if an element is displayed "" => "none" => ""
        window.setTimeout(function(){ circle.remove() },800); // => animation is 600ms
    }
    
    ret.refreshUI = function(rootElement)
    {
        const buttons = rootElement ? mx._$$(".form.button",rootElement) : mx.$$(".form.button");
        for (const button of buttons) 
        {
            if( button.dataset.ripple ) continue;

            button.dataset.ripple = 1
            button.addEventListener("click", createRipple);
        }
    }
    
    ret.init = function()
    {
        ret.refreshUI(document);
    };

    return ret;
})( mx.Page || {} );
