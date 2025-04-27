document.addEventListener('DOMContentLoaded', function() {
    let updateProductList = [];  // Declarar la lista de productos solo una vez

    // 🟢 Detectar clic en los botones de editar
    document.querySelectorAll('.edit-invoice-btn').forEach(button => {
        button.addEventListener('click', function() {
            const invoiceId = this.getAttribute('data-invoice-id');
            console.log('Factura seleccionada: ' + invoiceId);

            if (!invoiceId) {
                alert('No se encontró el ID de la factura.');
                return;
            }

            document.getElementById('update_invoice_id').value = invoiceId;
            loadInvoiceData(invoiceId);
        });
    });

    // 🟡 Cargar productos y estado de la factura
    function loadInvoiceData(invoiceId) {
        console.log('Cargando factura ID:', invoiceId);

        fetch(`/get_invoice_data/${invoiceId}`)
            .then(response => response.json())
            .then(data => {
                console.log('Datos recibidos:', data);

                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }

                document.getElementById('update_status').value = data.status;
                updateProductList = [];
                document.getElementById('update_productListBody').innerHTML = '';

                data.products.forEach(product => {
                    updateProductList.push({
                        imei: product.imei,
                        quantity: product.quantity,
                        price: product.price
                    });

                    const row = `
                        <tr data-imei="${product.imei}">
                            <td>${product.imei}</td>
                            <td>${product.name}</td>
                            <td>${product.storage}</td>
                            <td>${product.battery}</td>
                            <td>${product.color}</td>
                            <td class="text-center">${product.quantity}</td> 
                            <td><input type="text" class="form-control form-control-sm text-center update-price" value="${product.price}"></td>
                            <td class="text-center">
                                <button type="button" class="btn btn-danger btn-sm delete-product">🗑️</button>
                            </td>
                        </tr>`;
                    document.getElementById('update_productListBody').insertAdjacentHTML('beforeend', row);
                });
            })
            .catch(error => console.error('Error al obtener datos de la factura:', error));
    }

    // 🟢 Buscar producto por IMEI
    document.getElementById('update_imei').addEventListener('blur', function() {
        const imei = this.value.trim();
        if (imei === '') return;

        fetch(`/get_product_by_imei/${imei}`)
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    document.getElementById('update_imeiAlert').classList.remove('d-none');
                    clearProductFields();
                } else {
                    document.getElementById('update_imeiAlert').classList.add('d-none');
                    const product = data.product;
                    document.getElementById('update_product_name').value = product.productname;
                    document.getElementById('update_storage').value = product.storage;
                    document.getElementById('update_battery').value = product.battery;
                    document.getElementById('update_color').value = product.color;
                    document.getElementById('update_units').value = product.units;

                    
                    const quantityInput = document.getElementById('update_quantity');
                    quantityInput.max = product.units;  
                    quantityInput.value = '';           
                }
            })
            .catch(error => console.error('Error al buscar producto:', error));
    });


    // 🟢 Limpiar campos del producto
    function clearProductFields() {
        document.getElementById('update_product_name').value = '';
        document.getElementById('update_storage').value = '';
        document.getElementById('update_battery').value = '';
        document.getElementById('update_color').value = '';
        document.getElementById('update_units').value = '';
        document.getElementById('update_price').value = '';
    }

    // 🟢 Agregar producto a la tabla
    document.getElementById('updateProductButton').addEventListener('click', function() {
        const imei = document.getElementById('update_imei').value.trim();
        const name = document.getElementById('update_product_name').value.trim();
        const storage = document.getElementById('update_storage').value.trim();
        const battery = document.getElementById('update_battery').value.trim();
        const color = document.getElementById('update_color').value.trim();
        const quantity = parseInt(document.getElementById('update_quantity').value.trim(), 10);
        const availableUnits = parseInt(document.getElementById('update_units').value.trim(), 10);
        const price = parseFloat(document.getElementById('update_price').value.trim());

        if (imei === '' || name === '' || isNaN(quantity) || isNaN(price)) {
            alert('Por favor complete todos los campos del producto.');
            return;
        }

        if (quantity <= 0) {
            alert('La cantidad debe ser mayor a cero.');
            return;
        }

        if (quantity > availableUnits) {
            alert('La cantidad supera las unidades disponibles.');
            return;
        }

        const existingIndex = updateProductList.findIndex(p => p.imei === imei);
        if (existingIndex !== -1) {
            alert('Este producto ya está en la lista.');
            return;
        }

        updateProductList.push({ imei, quantity, price });

        const row = `
            <tr data-imei="${imei}">
                <td>${imei}</td>
                <td>${name}</td>
                <td>${storage}</td>
                <td>${battery}</td>
                <td>${color}</td>
                <td class="text-center">${quantity}</td>
                <td><input type="text" class="form-control form-control-sm text-center update-price" value="${price}"></td>
                <td class="text-center">
                    <button type="button" class="btn btn-danger btn-sm delete-product">🗑️</button>
                </td>
            </tr>`;
        document.getElementById('update_productListBody').insertAdjacentHTML('beforeend', row);

        clearProductFields();
        document.getElementById('update_imei').value = '';
    });

    // 🟢 Eliminar producto de la tabla y de la lista
    document.getElementById('update_productListBody').addEventListener('click', function(event) {
        if (event.target.classList.contains('delete-product')) {
            const row = event.target.closest('tr');
            const imei = row.getAttribute('data-imei');
            updateProductList = updateProductList.filter(p => p.imei !== imei);
            row.remove();
        }
    });

    // 🟢 Actualizar precio si cambia (cantidad no editable)
    document.getElementById('update_productListBody').addEventListener('input', function(event) {
        const row = event.target.closest('tr');
        const imei = row.getAttribute('data-imei');
        const price = parseFloat(row.querySelector('.update-price').value);

        const product = updateProductList.find(p => p.imei === imei);
        if (product) {
            product.price = price;
        }
    });

    // 🟢 Guardar cambios (enviar productos como JSON)
    document.getElementById('saveChangesButton').addEventListener('click', function() {
        const invoiceForm = this.closest('form');
        const productsInput = document.createElement('input');
        productsInput.type = 'hidden';
        productsInput.name = 'products';
        productsInput.value = JSON.stringify(updateProductList);
        invoiceForm.appendChild(productsInput);
        invoiceForm.submit();
    });
});
