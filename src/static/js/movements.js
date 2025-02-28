function approveMovement(movementId) {
    fetch(`/approve_movement/${movementId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();  // Recargar la página para actualizar la lista
    })
    .catch(error => console.error("Error:", error));
}

function rejectMovement(movementId) {
    let reason = prompt("Ingrese la razón del rechazo:");
    if (reason === null) return;

    fetch(`/reject_movement/${movementId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: reason })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();  // Recargar la página
    })
    .catch(error => console.error("Error:", error));
}
