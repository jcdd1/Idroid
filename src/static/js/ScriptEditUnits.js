document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ ScriptEditUnits.js cargado correctamente");

    const unitFields = document.querySelectorAll('.unit-field');
    if (unitFields.length === 0) console.error("⚠️ No se encontraron campos de unidades.");

    unitFields.forEach(field => {
        const unitDisplay = field.querySelector('.unit-display');
        const editButton = field.querySelector('.btn-edit-units');
        const editorDiv = field.querySelector('.unit-editor');
        const cancelButton = field.querySelector('.btn-cancel-edit');
        const addButton = field.querySelector('.btn-add');
        const subtractButton = field.querySelector('.btn-subtract');
        const inputField = field.querySelector('.unit-input');

        // Obtener warehouse_id asociado
        const warehouseId = field.getAttribute('data-warehouse-id'); // Obtén el warehouse_id

        // Aplicar estilo verde al botón Editar
        editButton.classList.remove('btn-primary');
        editButton.classList.add('btn-success');

        if (!unitDisplay || !editButton || !editorDiv) {
            console.error("⚠️ Faltan elementos en el campo de unidades:", field);
            return;
        }

        // Mostrar el editor al hacer clic en Editar
        editButton.addEventListener('click', function() {
            console.log(`✏️ Editando unidades para IMEI: ${field.getAttribute('data-imei')}`);
            unitDisplay.classList.add('d-none');
            editButton.classList.add('d-none');
            editorDiv.classList.remove('d-none');
        });

        // Cancelar edición
        cancelButton.addEventListener('click', function() {
            console.log(`🚫 Edición cancelada para IMEI: ${field.getAttribute('data-imei')}`);
            editorDiv.classList.add('d-none');
            unitDisplay.classList.remove('d-none');
            editButton.classList.remove('d-none');
            inputField.value = unitDisplay.textContent;
        });

        // Incrementar unidades
        addButton.addEventListener('click', function() {
            console.log(`➕ Incrementando unidades para IMEI: ${field.getAttribute('data-imei')}`);
            updateUnits(field.getAttribute('data-imei'), 1, inputField, unitDisplay, warehouseId); // Pasar warehouseId
        });

        // Disminuir unidades
        subtractButton.addEventListener('click', function() {
            console.log(`➖ Disminuyendo unidades para IMEI: ${field.getAttribute('data-imei')}`);
            updateUnits(field.getAttribute('data-imei'), -1, inputField, unitDisplay, warehouseId); // Pasar warehouseId
        });
    });

    // 🌐 Actualizar unidades en el servidor
    function updateUnits(imei, amount, input, display, warehouseId) {
        console.log(`📡 Enviando actualización para IMEI: ${imei} | Cantidad: ${amount} | Bodega: ${warehouseId}`);
        fetch(`/update_units/${imei}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({ 
                amount: amount,
                warehouse_id: warehouseId  // Enviar warehouse_id junto con amount
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`✅ Actualización exitosa: IMEI: ${imei}, Nuevas unidades: ${data.new_units}`);
                input.value = data.new_units;
                display.textContent = data.new_units;
            } else {
                console.error(`❌ Error al actualizar: ${data.message}`);
                alert('⚠️ Error al actualizar las unidades: ' + data.message);
            }
        })
        .catch(error => console.error('❌ Error en la petición:', error));
    }
});
