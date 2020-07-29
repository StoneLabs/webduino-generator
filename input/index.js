function setIntervalAndExecute(fn, t) {
    fn();
    return(setInterval(fn, t));
}

var timeoutId = 0;
function clicked()
{
    $.ajax({
        url: "toggleLed.cpp"
    });
}

/// Table builder from
/// https://stackoverflow.com/questions/5180382/convert-json-data-to-a-html-table
var myList; 

// Builds the HTML Table out of myList.
function buildHtmlTable(selector) {
    var columns = addAllColumnHeaders(myList, selector);

    for (var i = 0; i < myList.length; i++) {
        var row$ = $('<tr/>');
        for (var colIndex = 0; colIndex < columns.length; colIndex++) {
            var cellValue = myList[i][columns[colIndex]];
            if (cellValue == null) cellValue = "";
            row$.append($('<td/>').html(cellValue));
        }
        $(selector).append(row$);
    }
}

// Adds a header row to the table and returns the set of columns.
// Need to do union of keys from all records as some records may not contain
// all records.
function addAllColumnHeaders(myList, selector) {
    var columnSet = [];
    var headerTr$ = $('<tr/>');

    for (var i = 0; i < myList.length; i++) {
        var rowHash = myList[i];
        for (var key in rowHash) {
            if ($.inArray(key, columnSet) == -1) {
                columnSet.push(key);
                headerTr$.append($('<th/>').html(key));
            }
        }
    }
    $(selector).append(headerTr$);

    return columnSet;
}
function loadTable()
{
    // Pin Table ajax
    
}

$( document ).ready(function(){
    // Button click event handler
    $( ".obj" ).on('mousedown', function() {
        timeoutId = setTimeout(clicked, 400);
    }).on('mouseup mouseleave', function() {
        clearTimeout(timeoutId);
    });

    setIntervalAndExecute(function(){
        $.ajax({
            url: "jsonStatus.cpp"
        }).done(function( data ) {
            myList = data;
            $("#pinTable").html("");
            buildHtmlTable('#pinTable');
        })
    }, 2000);
});