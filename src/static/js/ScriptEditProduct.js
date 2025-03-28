document.addEventListener('DOMContentLoaded', function () {
    const editProductModal = document.getElementById('editProductModal');
    editProductModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget; // Botón que disparó el modal
        const productData = button.getAttribute('data-product'); // Datos JSON
        const invoicesData = button.getAttribute('data-invoices');

        if (!productData) {
            console.error("No se encontraron datos para el producto.");
            return;
        }

        //Obtener el elemento select para las facturas
        const invoiceSelect = document.getElementById('edit_invoice');
        const quantityInput = document.getElementById('edit_quantity');
        const priceInput = document.getElementById('edit_price');

        const product = JSON.parse(productData);
        const invoices = JSON.parse(invoicesData);

        // Limpiar las opciones existentes
        invoiceSelect.innerHTML = '<option value="">Seleccione una factura</option>';
        
        // Agregar las facturas activas al select
        invoices.forEach(invoice => {
            const option = document.createElement('option');
            option.value = invoice.document_number;
            option.textContent = invoice.document_number;
            invoiceSelect.appendChild(option);
            //console.log(invoice.document_number)
        });

        // Configurar el valor máximo para la cantidad según el producto
        const maxUnits = product.units;
        quantityInput.setAttribute('max', maxUnits);

        // Deshabilitar cantidad inicialmente
        quantityInput.disabled = true;
        priceInput.disabled = true;
        

        // Habilitar cantidad al seleccionar una factura
        invoiceSelect.addEventListener('change', function () {
            if (invoiceSelect.value) {
                quantityInput.disabled = false; // Habilitar el campo
                priceInput.disabled = false;
            } else {
                quantityInput.disabled = true; // Deshabilitar si no hay factura seleccionada
                priceInput.disabled = true;
            }
        });

        // Validar cantidad ingresada
        quantityInput.addEventListener('input', function () {
            const value = parseInt(quantityInput.value, 10);
            if (value > maxUnits) {
                quantityInput.value = maxUnits; // No permitir más del inventario
            } else if (value < 1) {
                quantityInput.value = 1; // No permitir menos de 1
            }
        });

        console.log("Product Data:", productData);
        console.log("Parsed Product:", product);

        //document_number
        // Asigna valores a los campos del modal
        document.getElementById('edit_product_id').value = product.product_id || "";
        document.getElementById('edit_warehouse_id').value = product.warehouse_id || "";
        document.getElementById('edit_productname').value = product.productname || "";
        document.getElementById('edit_imei').value = product.imei || "";
        document.getElementById('edit_storage').value = product.storage || "";
        document.getElementById('edit_battery').value = product.battery || "";
        document.getElementById('edit_color').value = product.color || "";
        document.getElementById('edit_cost').value = product.cost || "";
        document.getElementById('edit_price').value = product.price || "";
        document.getElementById('edit_category').value = product.category || "";
        document.getElementById('edit_units').value = product.units || "";
        document.getElementById('edit_supplier').value = product.supplier || "";
        document.getElementById('edit_current_status').value = product.current_status || "";
        if (product.creation_date) {
            const date = new Date(product.creation_date); // Crear un objeto Date
            const formattedDate = date.toISOString().split('T')[0]; // Convertir a YYYY-MM-DD
            document.getElementById('edit_creation_date').value = formattedDate;
        }
        document.getElementById('edit_description').value = product.description || "";
    });
});
