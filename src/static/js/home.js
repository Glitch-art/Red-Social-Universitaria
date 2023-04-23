function editPost(id){
    formulario = document.getElementById('formulario');
    btn = document.getElementById('btn');

    tabla_description = document.getElementById(`tabla_description${id}`);
    tabla_content = document.getElementById(`tabla_content${id}`);

    form_post_description = document.getElementById(`form_post_description`);
    form_post_content = document.getElementById(`form_post_content`);
    form_post_content_image = document.getElementById(`form_post_content_image`);

    form_post_description.value = tabla_description.innerHTML
    if (obtenerRutaDeImagen(tabla_content)) {
        form_post_content_image.src = obtenerRutaDeImagen(tabla_content);
        form_post_content_image.classList.remove("d-none");
    } else {
        form_post_content_image.classList.add("d-none");
    }

    formulario.action = `/edit_post/${id}`;
    btn.innerHTML = 'Actualizar';
}

function obtenerRutaDeImagen(tdConImagen) {
    // Comprobar si el td contiene un elemento hijo (en este caso, la imagen)
    if (tdConImagen.childElementCount > 0) {
        // Obtener el elemento img
        const img = tdConImagen.querySelector('img');
    
        // Obtener la ruta de la imagen
        const rutaDeImagen = img.getAttribute('src');
        
        return rutaDeImagen;
    } else {
        return null;
    }
}
  