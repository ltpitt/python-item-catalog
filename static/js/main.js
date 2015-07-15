if (document.getElementById('inputItemImage')) {
    var imageLoader = document.getElementById('inputItemImage');
    imageLoader.addEventListener('change', handleImage, false);
}

function handleImage(e){
    var reader = new FileReader();
    reader.onload = function(event){
        var img = new Image();
        $('.cropper > img').cropper("destroy");
        img.onload = function(){
            startCropper();
        }
        $('#item-image').show();
        $('#item-image').attr('src', event.target.result);
        img.src = event.target.result;
    }
    reader.readAsDataURL(e.target.files[0]);
}


/*
$('#confirm-delete').on('show.bs.modal', function(e) {
    $(this).find('.btn-ok').attr('href', $(e.relatedTarget).data('href'));
});


if (document.getElementById('inputItemImage')) {
    var imageLoader = document.getElementById('inputItemImage');
    imageLoader.addEventListener('change', handleImage, false);
}

function handleImage(e){
    var reader = new FileReader();
    reader.onload = function(event){
        var img = new Image();
        $('.cropper > img').cropper("destroy");
        img.onload = function(){
            startCropper();
        }
        $('#item-image').show();
        $('#item-image').attr('src', event.target.result);
        img.src = event.target.result;
    }
    reader.readAsDataURL(e.target.files[0]);
}

function startCropper() {
    $('.cropper > img').cropper({
      guides: true,
      highlight: false,
      dragCrop: false,
      cropBoxMovable: false,
      cropBoxResizable: false,
      crop: function(data) {
      console.log(imageLoader.data);


        // Begin form send
        $.ajax({
            beforeSend: function() {
               //Show spinner
            },
            complete: function() {
                //Hide spinner
            },
            url: '',
            dataType: 'json',
            headers: 'headers',
            success: function(data) {
                // Insert actions here
            } // fine di success
        });
// End form send


      },
      responsive: true,
      rotatable: true,
      minCropBoxWidth: 800,
      minCropBoxHeight: 300,
    });
}

function cropperCrop() {
    $('.cropper > img').cropper("crop");
}

*/