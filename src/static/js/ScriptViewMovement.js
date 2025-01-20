document.addEventListener('DOMContentLoaded', function () {
    const viewMovementsModal = document.getElementById('viewMovementsModal');

    viewMovementsModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget; // Botón que disparó el modal
        const imei = button.getAttribute('data-imei'); // IMEI del producto

        // Limpia el contenido del cuerpo de la tabla antes de cargar nuevos datos
        const tableBody = document.getElementById('movementsTableBody');
        tableBody.innerHTML = ''; 

        // Realiza una solicitud AJAX para obtener los movimientos
        fetch(`/movements/${imei}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.movements && data.movements.length > 0) {
                    // Llena la tabla con los movimientos obtenidos
                    data.movements.forEach(movement => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${movement.movement_id || 'N/A'}</td>
                            <td>${movement.movement_type || 'N/A'}</td>
                            <td>${movement.creation_date || 'N/A'}</td>
                            <td>${movement.movement_status || 'N/A'}</td>
                            <td>${movement.origin_warehouse_id || 'N/A'}</td>
                            <td>${movement.origin_warehouse_name || 'N/A'}</td>
                            <td>${movement.destination_warehouse_id || 'N/A'}</td>
                            <td>${movement.destination_warehouse_name || 'N/A'}</td>
                            <td>${movement.movement_quantity || 'N/A'}</td>
                            <td>${movement.detail_status || 'N/A'}</td>
                            <td>${movement.rejection_reason || 'N/A'}</td>
                            <td>${movement.return_id || 'N/A'}</td>
                            <td>${movement.returned_quantity || 'N/A'}</td>
                            <td>${movement.return_date || 'N/A'}</td>
                            <td>${movement.return_notes || 'N/A'}</td>
                        `;
                        tableBody.appendChild(row);
                    });
                } else {
                    // Si no hay movimientos, muestra un mensaje en la tabla
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td colspan="15" class="text-center">No hay movimientos disponibles para este producto.</td>
                    `;
                    tableBody.appendChild(row);
                }
            })
            .catch(error => {
                console.error('Error fetching movements:', error);

                // Muestra un mensaje de error en la tabla
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td colspan="15" class="text-center text-danger">Error al cargar los movimientos. Intenta nuevamente.</td>
                `;
                tableBody.appendChild(row);
            });
    });
});
