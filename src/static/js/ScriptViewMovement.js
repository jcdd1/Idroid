document.addEventListener('DOMContentLoaded', function () {
    const viewMovementsModal = document.getElementById('viewMovementsModal');
    const tableBody = document.getElementById('movementsTableBody');

    // Evento al mostrar el modal
    viewMovementsModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget; // Botón que disparó el modal
        const imei = button.getAttribute('data-imei'); // IMEI del producto
        tableBody.innerHTML = ''; // Limpia el contenido anterior

        // Llamada para obtener los movimientos
        fetch(`/movements/${imei}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.movements && data.movements.length > 0) {
                    data.movements.forEach(movement => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td class="text-center">${movement.movement_id || 'N/A'}</td>
                            <td class="text-center">${movement.movement_type || 'N/A'}</td>
                            <td class="text-center">${formatDate(movement.creation_date) || 'N/A'}</td>
                            <td class="text-center">${movement.origin_warehouse_name || 'N/A'}</td>
                            <td class="text-center">${movement.destination_warehouse_name || 'N/A'}</td>
                            <td class="text-center">${movement.status || 'N/A'}</td>
                            <td class="text-center">${movement.movement_quantity || 'N/A'}</td>
                            <td class="text-center">${movement.detail_status || 'N/A'}</td>
                            <td class="text-center">${movement.rejection_reason || 'N/A'}</td>
                            <td class="text-center">${movement.return_id || 'N/A'}</td>
                            <td class="text-center">${movement.returned_quantity || 'N/A'}</td>
                            <td class="text-center">${formatDate(movement.return_date) || 'N/A'}</td>
                            <td class="text-center">${movement.return_notes || 'N/A'}</td>
                        `;
                        tableBody.appendChild(row);
                    });
                } else {
                    tableBody.innerHTML = `
                        <tr>
                            <td colspan="13" class="text-center text-muted">⚠️ No hay movimientos disponibles para este producto.</td>
                        </tr>`;
                }
            })
            .catch(error => {
                console.error('❌ Error al cargar los movimientos:', error);
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="13" class="text-center text-danger">❌ Error al cargar los movimientos. Intenta nuevamente.</td>
                    </tr>`;
            });
    });

    // 📅 Formatear fechas al formato legible
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1)
            .toString().padStart(2, '0')}/${date.getFullYear()} ${date.getHours()
            .toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
});
