
function obtenerDatos(id){
    formulario = document.getElementById('formulario')
    btn = document.getElementById('btn')
    
    tabla_nombre = document.getElementById(`tabla_nombre${id}`)
    tabla_valor = document.getElementById(`tabla_valor${id}`)
    tabla_cantidad = document.getElementById(`tabla_cantidad${id}`)

    nombre = document.getElementById(`nombre`)
    valor = document.getElementById(`valor`)
    cantidad = document.getElementById(`cantidad`)

    nombre.value = tabla_nombre.innerHTML
    valor.value = tabla_valor.innerHTML
    cantidad.value = tabla_cantidad.innerHTML

    formulario.action = `/editar_producto/${id}`
    btn.innerHTML = 'Actualizar'
}