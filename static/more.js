var refresh = new Event("refresh");

document.addEventListener("refresh", function () {
        setInterval(
            function (){
                lookup()
            }
            , 60000)
});

function lookup()
{
    $.ajax(
        {
            type: "POST",
            url: "/lookup",
            success: function (d) {
                update_price(d);
                console.log(d);
            }
        }
    )
}


function update_price(symbols)
{
    for (var symbol in symbols)
    {
        var tr = document.getElementById(symbol);
        var changes = tr.innerHTML;
        var current_changes = document.getElementById(`${symbol}_c`);
        tr.innerHTML = symbols[symbol][0];
        if (changes)
        {
            current_changes.innerHTML = parseFloat(symbols[symbol][0]) - parseFloat(symbols[symbol][1]);

        }
    }
}


document.dispatchEvent(refresh)




