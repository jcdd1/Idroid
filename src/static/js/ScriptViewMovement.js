document.addEventListener('DOMContentLoaded', function () {
    const viewMovementsModal = document.getElementById('viewMovementsModal');

    viewMovementsModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget; // Botón que disparó el modal
        const imei = button.getAttribute('data-imei'); // IMEI del producto

        // Realiza una solicitud AJAX para obtener los movimientos
        fetch(`/movements/${imei}`)
            .then(response => response.json())
            .then(data => {
                const tableBody = document.getElementById('movementsTableBody');
                tableBody.innerHTML = ''; // Limpia el contenido actual

                // Llena la tabla con los movimientos obtenidos
                data.movements.forEach(movement => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${movement.movement_id}</td>
                        <td>${movement.origin_warehouse_id}</td>
                        <td>${movement.destination_warehouse_id}</td>
                        <td>${movement.sender_user_id}</td>
                        <td>${movement.receiver_user_id}</td>
                        <td>${movement.send_date}</td>
                        <td>${movement.receive_date}</td>
                        <td>${movement.movement_status}</td>
                        <td>${movement.movement_description}</td>
                    `;
                    tableBody.appendChild(row);
                });
            })
            .catch(error => {
                console.error('Error fetching movements:', error);
            });
    });
});
