document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript movement.js está corriendo correctamente.");

    document.querySelectorAll(".approve-btn").forEach(button => {
        button.addEventListener("click", function () {
            const movementId = this.getAttribute("data-movement-id");
            console.log(`Aprobando movimiento: ${movementId}`);
            approveMovement(movementId);
        });
    });

    document.querySelectorAll(".reject-btn").forEach(button => {
        button.addEventListener("click", function () {
            const movementId = this.getAttribute("data-movement-id");
            console.log(`Rechazando movimiento: ${movementId}`);
            rejectMovement(movementId);
        });
    });
});

function approveMovement(movementId) {
    console.log(`Enviando solicitud para aprobar movimiento ${movementId}`);

    // Obtener CSRF Token desde el <meta>
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/approve_movement/${movementId}`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken  // Agregar CSRF Token aquí
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text); });
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        location.reload();
    })
    .catch(error => {
        console.error("Error en approveMovement:", error);
        alert("Ocurrió un error al aprobar el movimiento. Ver consola.");
    });
}

function rejectMovement(movementId) {
    let reason = prompt("Ingrese la razón del rechazo:");
    if (reason === null || reason.trim() === "") {
        alert("Debe ingresar una razón válida.");
        return;
    }

    console.log(`Enviando solicitud para rechazar movimiento ${movementId} con razón: ${reason}`);

    // Obtener CSRF Token desde el <meta>
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch(`/reject_movement/${movementId}`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken  // Agregar CSRF Token aquí
        },
        body: JSON.stringify({ reason: reason })
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => { throw new Error(text); });
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        location.reload();
    })
    .catch(error => {
        console.error("Error en rejectMovement:", error);
        alert("Ocurrió un error al rechazar el movimiento. Ver consola.");
    });
}
