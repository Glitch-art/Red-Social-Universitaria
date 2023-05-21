function editAcademicFile(id){
    formulario = document.getElementById('formulario');
    btn = document.getElementById('btn');

    tabla_teacher_id = document.getElementById(`tabla_teacher_id${id}`);
    tabla_name = document.getElementById(`tabla_name${id}`);
    tabla_content = document.getElementById(`tabla_content${id}`);

    form_academic_file_teacher_id = document.getElementById(`form_academic_file_teacher_id`);
    form_academic_file_name = document.getElementById(`form_academic_file_name`);
    form_academic_file_content_image = document.getElementById(`form_academic_file_content_image`);
    form_academic_file_content = document.getElementById(`form_academic_file_content`);

    form_academic_file_name.value = tabla_name.innerHTML
    if (obtenerRutaDeImagen(tabla_content)) {
        form_academic_file_content_image.src = obtenerRutaDeImagen(tabla_content);
        form_academic_file_content_image.classList.remove("d-none");
    } else {
        form_academic_file_content_image.classList.add("d-none");
    }

    // Reemplazar el teacher_id del formulario con el teacher_id de la tabla
    // Se recorren las opciones del select del formulario
    for (let i = 0; i < form_academic_file_teacher_id.options.length; i++) {
        let option = form_academic_file_teacher_id.options[i];
        // Se compara el contenido de la opción con tabla_teacher_id
        if (option.value == tabla_teacher_id.innerHTML) {
            // Se establece el índice de la opción seleccionada
            form_academic_file_teacher_id.selectedIndex = i;
            break;
        }
    }

    formulario.action = `/edit_academic_file/${id}`;
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
