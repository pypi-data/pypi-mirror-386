
window.requirejs.config( { paths : { $toolName : $CDNURL } } );

window.VisualizationTools.$toolName = function ( element, json, callback ) {
    require( [ $toolString ],
        function ( $toolName ) { $functionBody } );
};
