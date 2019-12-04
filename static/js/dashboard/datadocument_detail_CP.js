$(document).ready(function () {
    $('#id_chems').change(function () {
        if (this.value) {
            $('#keyword-save').attr('disabled', false)
        } else {
            $('#keyword-save').attr('disabled', true)
        }
    })
});

$('[id^=chem-click-]').click(function (e) {
    // add outline to card and add/remove chemicalID to value string in input
    var inputs = $("#id_chems")[0];
    var chemList = inputs.value.split(",");
    chemList = chemList.filter(function (entry) {
        return /\S/.test(entry);
    });
    var chemId = $(this).attr("data-chem-id");
    var index = $.inArray(chemId, chemList);
    if (index == -1) {
        this.style.outline = "4px solid rgba(243, 240, 87, 0.47)";
        chemList.push(chemId);
    } else {
        this.style.outline = ""
        chemList.splice(index, 1);
    }
    $('#selected').text(chemList.length);
    $(inputs).attr("value", chemList.join(","));
    // with no chems selected, the save buton should be disabled
    $("#id_chems").trigger('change');
})

$('#select-all-chems').click(function (e) {
    var titulo = $(this).attr("data-original-title")
    var chemList = [];
    var inputs = $("#id_chems")[0];
    if (titulo === "Select All Chemicals") {
        $(this).attr("data-original-title", "Deselect All Chemicals")
        switchIcons(this);
        $('[id^=chem-click-]').each(function (i) {
            var chemId = $(this).attr("data-chem-id");
            chemList.push(chemId);
            this.style.outline = "4px solid rgba(243, 240, 87, 0.47)";
        });
    } else {
        $(this).attr("data-original-title", "Select All Chemicals")
        switchIcons(this);
        $('[id^=chem-click-]').each(function (i) {
            this.style.outline = "";
        });
    }
    $('#selected').text(chemList.length);
    $(inputs).attr("value", chemList.join(","));
    $("#id_chems").trigger('change');
});

function switchIcons(elem) {
    $(elem).find('#select-all').toggleClass('d-none')
    $(elem).find('#select-none').toggleClass('d-none')
};
