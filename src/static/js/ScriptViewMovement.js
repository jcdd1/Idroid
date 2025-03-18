document.addEventListener('DOMContentLoaded', function () {
    const viewMovementsModal = document.getElementById('viewMovementsModal');
    const tableBody = document.getElementById('movementsTableBody');

    // Evento al mostrar el modal
    viewMovementsModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        const imei = button.getAttribute('data-imei');
    
        tableBody.innerHTML = `<tr><td colspan="13" class="text-center text-warning">⏳ Cargando movimientos...</td></tr>`;
    
        setTimeout(() => { // Agregamos un pequeño retraso
            fetch(`/movements/${imei}`)
                .then(response => response.json())
                .then(data => {
                    tableBody.innerHTML = ''; // Limpiar antes de insertar nuevas filas
    
                    if (data.movements && data.movements.length > 0) {
                        data.movements.forEach(movement => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${movement.movement_id || 'N/A'}</td>
                                <td>${movement.origin_warehouse || 'N/A'}</td>
                                <td>${movement.destination_warehouse || 'N/A'}</td>
                                <td>${formatDate(movement.creation_date) || 'N/A'}</td>
                                <td>${movement.movement_status || 'N/A'}</td>
                                <td>${movement.movement_notes || 'N/A'}</td>
                                <td>${movement.movement_type || 'N/A'}</td>
                                <td>${movement.created_by_user || 'N/A'}</td>
                                <td>${movement.handled_by_user || 'N/A'}</td>
                                <td>${movement.moved_quantity || 'N/A'}</td>
                                <td>${movement.detail_status || 'N/A'}</td>
                                <td>${movement.rejection_reason || 'N/A'}</td>
                                <td>${movement.returned_quantity || 'N/A'}</td>
                                <td>${formatDate(movement.return_date) || 'N/A'}</td>
                                <td>${movement.return_notes || 'N/A'}</td>
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
                    tableBody.innerHTML = `<tr><td colspan="13" class="text-center text-danger">❌ Error al cargar los movimientos. Intenta nuevamente.</td></tr>`;
                });
        }, 300); // Agregamos un retraso de 300ms
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
