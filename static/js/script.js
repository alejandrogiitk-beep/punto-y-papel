
document.addEventListener("DOMContentLoaded", () => {

    // =================================
    // VALIDACION DEL REGISTRO
    // =================================

    const registro = document.querySelector("#formRegistro");

    if (registro) {
        registro.addEventListener("submit", (evento) => {

            const nombre = document.querySelector("#nombre").value.trim();
            const password = document.querySelector("#password").value;

            if (nombre.length < 3) {
                evento.preventDefault();
                alert("El nombre debe tener al menos 3 caracteres.");
                return;
            }

            if (password.length < 8) {
                evento.preventDefault();
                alert("La contraseña debe tener al menos 8 caracteres.");
            }
        });
    }

    // =================================
    // VALIDACION DE PRODUCTOS
    // =================================

    const formulario = document.querySelector("#formProducto");

    if (formulario) {
        formulario.addEventListener("submit", (evento) => {

            const precio = Number(
                document.querySelector("#precio").value
            );

            const stock = Number(
                document.querySelector("#stock").value
            );

            if (!Number.isFinite(precio) || precio <= 0) {
                evento.preventDefault();
                alert("El precio debe ser mayor a cero.");
                return;
            }

            if (!Number.isInteger(stock) || stock < 0) {
                evento.preventDefault();
                alert("El stock debe ser un entero no negativo.");
            }
        });
    }

    // =================================
    // BUSCADOR EN TIEMPO REAL
    // =================================

    const buscador = document.querySelector("#buscador");

    if (buscador) {

        let temporizador;

        buscador.addEventListener("input", () => {

            clearTimeout(temporizador);

            const termino = buscador.value.trim();
            const cuerpo = document.querySelector(
                "#tablaProductos tbody"
            );

            temporizador = setTimeout(async () => {

                try {
                    const respuesta = await fetch(
                        "/api/productos?q=" +
                        encodeURIComponent(termino)
                    );

                    if (!respuesta.ok) {
                        throw new Error("Error en la consulta");
                    }

                    const datos = await respuesta.json();

                    cuerpo.replaceChildren();

                    datos.forEach(producto => {

                        const fila = document.createElement("tr");

                        const valores = [
                            producto.nombre,
                            producto.categoria,
                            "$" + Number(producto.precio).toFixed(2),
                            producto.stock
                        ];

                        valores.forEach(valor => {
                            const celda = document.createElement("td");
                            celda.textContent = valor;
                            fila.appendChild(celda);
                        });

                        const acciones = document.createElement("td");
                        acciones.textContent =
                            "Utiliza las opciones de edicion del inventario.";

                        fila.appendChild(acciones);
                        cuerpo.appendChild(fila);
                    });

                    document.querySelector("#contador").textContent =
                        datos.length + " productos encontrados.";

                } catch (error) {
                    console.error(error);
                    document.querySelector("#contador").textContent =
                        "No fue posible consultar los productos.";
                }

            }, 250);
        });
    }

});
