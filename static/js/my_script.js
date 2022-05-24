function addImage() {
    let count = $(".image").length + 1;
    $(".btn-add").before("<div class='input-group mb-3 image'><input type='file' class='form-control' id='file' name='file" + count + "' required><button type='button' class='btn btn-danger' onclick='removeImage($(this))'>-</button></div>");
};
function removeImage(btn) {
    $(btn).parent().remove();
}
function remove(btn, image_id, recipe_id) {
//
    $.ajax('/delete_img/', {
    type: 'POST',  // http method
    data: { "image_id": image_id,
            "recipe_id": recipe_id},  // data to submit
    success: function (data, status, xhr) {
        $(btn).parent().parent().remove();
    },
    error: function (data, textStatus, errorMessage) {
        console.log(textStatus + ":can't delete image: " + errorMessage);
    }
});
}