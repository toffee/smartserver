var mxTheme = document.cookie.split( ';' ).map( function( x ) { return x.trim().split( '=' ); } ).reduce( function( a, b ) { a[ b[ 0 ] ] = b[ 1 ]; return a; }, {} )[ "theme" ];

var css = '';

if( mxTheme == 'light' )
{
    css += `
    
   `;
}
else if( mxTheme == 'dark' )
{
    css += `

   `;
}

var element = document.createElement('style');
element.type = 'text/css'; 
element.innerHTML = css;

document.getElementsByTagName("head")[0].appendChild(element); 
