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
                    <td>${movement.creation_date}</td>
                    <td>${movement.movement_status}</td>
                    <td>${movement.movement_notes}</td>
                    <td>${movement.detail_id}</td>
                    <td>${movement.product_id}</td>
                    <td>${movement.quantity}</td>
                    <td>${movement.detail_status}</td>
                    <td>${movement.rejection_reason ? movement.rejection_reason : 'N/A'}</td>
                    <td>${movement.return_id ? movement.return_id : 'N/A'}</td>
                    <td>${movement.returned_quantity ? movement.returned_quantity : 'N/A'}</td>
                    <td>${movement.return_date ? movement.return_date : 'N/A'}</td>
                    <td>${movement.return_notes ? movement.return_notes : 'N/A'}</td>
                `;
                    tableBody.appendChild(row);
                });
            })
            .catch(error => {
                console.error('Error fetching movements:', error);
            });
    });
});
