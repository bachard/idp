$(document).ready(function() {

    function toggleEdit() {
        $('button[data-type="send_data"] span').each(function() {
            $(this).removeClass("glyphicon-check")
                .addClass("glyphicon-edit")
                .removeClass("green")
                .addClass("blue");                
        });
    }

    function toggleCheck() {
        $('button[data-type="send_data"] span').each(function() {
            $(this).addClass("glyphicon-check")
                .removeClass("glyphicon-edit")
                .addClass("green")
                .removeClass("blue");
                
        });
    }
    
    $("input").on("change", toggleEdit);
    
    $('button[data-type="send_data"]').on("click", function() {
        
        var $this = $(this);
        var update_players = [];

        $("tr[data-id]").each(function(line) {
            var $line = $(this);
            var update_player = {id: $line.data("id")};
            $line.find("td input").each(function(input) {
                var $input = $(this);
                update_player[$input.parent().data("name")] = $input.val();
            });
            update_players.push(update_player);
        });
        
        
        
        var data = {
            session_nr: $this.data("id"),
            update_players: update_players
        };
        
        $.ajax({
            type: "POST",
            url: $this.data("target"),
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(res) {
                console.log(res);
                toggleCheck();
            },
            failure: function(err) {console.log(err);}            
        });
    });    
});
