// INDEX SPINNER CARGAR ARCHIVO
const uploadForm = document.getElementById("uploadForm");
if (uploadForm) {
    uploadForm.addEventListener("submit", function (event) {
        event.preventDefault(); // Evita la recarga de la página

        const spinner = document.getElementById("loadingSpinner");
        const successIcon = document.getElementById("successIcon");
        const modalMessage = document.getElementById("modalMessage");

        // Mostrar el modal de Bootstrap inmediatamente
        const loadingModal = new bootstrap.Modal(document.getElementById("loadingModal"));
        loadingModal.show();  // Esto abre el modal

        // Mostrar el spinner y ocultar el ícono de éxito
        spinner.style.display = "block";
        successIcon.style.display = "none";
        modalMessage.textContent = "Cargando archivo, por favor espera...";

        // Usamos FormData para enviar el archivo sin recargar la página
        const formData = new FormData(uploadForm);

        // Realizamos la solicitud fetch para enviar el archivo al servidor
        fetch("/upload", {
            method: "POST",
            body: formData,
        })
            .then(response => {
                if (response.ok) {
                    // Simulamos el éxito después de un retraso
                    setTimeout(() => {
                        spinner.style.display = "none";  // Ocultar el spinner
                        successIcon.style.display = "block";  // Mostrar el ícono de éxito
                        modalMessage.textContent = "Archivo cargado con éxito";

                        // Cerrar el modal después de 2 segundos
                        setTimeout(() => {
                            loadingModal.hide(); // Cierra el modal
                        }, 2000); // El modal se cierra 2 segundos después de mostrar el ícono de éxito

                        // Redirigir después de 4 segundos (opcional)
                        setTimeout(() => {
                            // window.location.href = "/analysis"; // Redirigir a la página de análisis
                        }, 4000); // Redirigir después de 4 segundos
                    }, 3000); // Simulamos un retraso de 3 segundos
                } else {
                    // En caso de error en la carga del archivo
                    modalMessage.textContent = "Hubo un error al cargar el archivo";
                }
            })
            .catch(error => {
                console.error("Error al subir el archivo:", error);
                modalMessage.textContent = "Hubo un error al cargar el archivo";
            });
    });
}


//ANALYZE SPINNER SELECCION DE ARCHIVO
document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('analyzeForm');
    var loadingModalElement = document.getElementById('loadingModal');
    var loadingSpinner = document.getElementById('loadingSpinner');

        var loadingModal = new bootstrap.Modal(loadingModalElement, {
            backdrop: 'static',
            keyboard: false
        });

    var successIcon = document.getElementById('successIcon');
    var modalMessage = document.getElementById('modalMessage');

    if (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault(); // Evita que el formulario se envíe de manera tradicional

            // Muestra el modal de carga
            loadingModal.show();

            // Obtén el archivo seleccionado
            var selectedFile = document.getElementById('file').value;

            // Realiza una solicitud fetch para analizar el archivo
            var formData = new FormData(form);

            // Muestra el modal durante un corto período de tiempo antes de continuar
            setTimeout(() => {
                fetch(form.action, {
                    method: form.method,
                    body: formData
                })
                    .then(response => {
                        if (response.ok) {
                            // Ocultar el spinner
                            loadingSpinner.style.display = 'none';

                            // Muestra el icono de éxito y el mensaje en el modal
                            successIcon.style.display = 'block';
                            modalMessage.innerHTML = '¡Archivo seleccionado correctamente!';

                            // Espera unos segundos y luego redirige al archivo analizado
                            setTimeout(() => {
                                window.location.href = `/analyze_file/${selectedFile}`;
                            }, 1500); // 1.5 segundos para mostrar el mensaje y el icono
                        } else {
                            // Oculta el modal y muestra un mensaje de error si algo falla
                            loadingModal.hide();
                            alert("Ocurrió un error al procesar el archivo. Inténtalo de nuevo.");
                        }
                    })
                    .catch(error => {
                        // Maneja errores en la solicitud
                        loadingModal.hide();
                        console.error("Error en la solicitud fetch:", error);
                        alert("Error en la solicitud. Por favor, revisa la consola para más detalles.");
                    });
            }, 500); // Espera 500 ms antes de realizar la solicitud
        });
    }




});


//UPLOADS SPINNER PARA ELIMINAR
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar el modal de carga
    var loadingModalElement = document.getElementById('loadingModal');
        var loadingModal = new bootstrap.Modal(loadingModalElement, {
            backdrop: 'static', // Evita que se cierre al hacer clic fuera del modal
            keyboard: false // Evita que se cierre con la tecla ESC
        });
  


    var successIcon = document.getElementById('successIcon');
    var modalMessage = document.getElementById('modalMessage');
    var loadingSpinner = document.getElementById('loadingSpinner');

    // Función para eliminar archivo
    var deleteButtons = document.querySelectorAll('.delete-btn');

    deleteButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            var fileName = this.getAttribute('data-file');
            var form = document.getElementById('deleteForm-' + fileName);

            // Muestra el modal de carga con el spinner
            loadingModal.show();

            // Después de 500ms, hacer la solicitud para eliminar el archivo
            setTimeout(function () {
                fetch(form.action, {
                    method: 'POST',
                    body: new FormData(form)
                })
                    .then(response => {
                        if (response.ok) {
                            // Oculta el spinner y muestra el icono de éxito
                            loadingSpinner.style.display = 'none';
                            successIcon.style.display = 'block';
                            modalMessage.innerHTML = '¡Archivo eliminado correctamente!';


                            // Espera 2 segundos antes de recargar la página
                            setTimeout(function () {
                                location.reload(); // Recarga la página para reflejar los cambios
                            }, 2000);
                        } else {
                            // En caso de error, muestra un mensaje de error
                            loadingModal.hide();
                            alert('Hubo un error al eliminar el archivo. Inténtalo nuevamente.');
                        }
                    })
                    .catch(function (error) {
                        // En caso de error en la solicitud
                        loadingModal.hide();
                        alert('Error en la solicitud. Por favor, revisa la consola para más detalles.');
                    });
            }, 500); // Espera 500ms para simular carga
        });
    });
});

