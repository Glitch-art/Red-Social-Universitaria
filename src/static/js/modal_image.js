function OpenModalImage(img_id) {
    // Get the modal
    var modal = document.getElementById("my_modal_image");

    // Get the image and insert it inside the modal - use its "alt" text as a caption
    var img = document.getElementById(img_id);
    var modalImg = document.getElementById("modal_image_id");
    var captionText = document.getElementById("caption");
    img.onclick = function(){
        modal.style.display = "block";
        modalImg.src = this.src;
        captionText.innerHTML = this.alt;
    }
    // Get the <span> element that closes the modal
    var span = document.getElementsByClassName("close_modal_image")[0];
    
    // When the user clicks on <span> (x), close the modal
    span.onclick = function() { 
        modal.style.display = "none";
    }
}
