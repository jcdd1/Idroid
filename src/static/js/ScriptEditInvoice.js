document.addEventListener('DOMContentLoaded', function () {
    const imeiInput = document.getElementById('imei');
    const createInvoiceButton = document.getElementById('createInvoiceButton');
    const alertBox = document.getElementById('imeiAlert');
    const closeButton = document.querySelector('#addInvoiceModal .btn-close');
    const modalElement = document.getElementById('addInvoiceModal');
    let typingTimer;
    const typingInterval = 500;

    // 🔄 Limpia los campos al cerrar el modal (X o botón "Cerrar")
    closeButton.addEventListener('click', clearFormFields);
    modalElement.addEventListener('hidden.bs.modal', clearFormFields);

    imeiInput.addEventListener('input', function () {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(fetchProductData, typingInterval);
    });

    function fetchProductData() {
        const imei = imeiInput.value.trim();
        if (imei.length >= 5) {
            fetch(`/get_product_by_imei/${imei}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('product_name').value = data.product.productname;
                        document.getElementById('storage').value = data.product.storage;
                        document.getElementById('battery').value = data.product.battery;
                        document.getElementById('color').value = data.product.color;
                        document.getElementById('units').value = data.product.units;

                        if (data.product.warehouse_id !== data.current_user_warehouse_id) {
                            createInvoiceButton.disabled = true;
                            alertBox.textContent = "⚠️ El producto no se encuentra en tu bodega.";
                            alertBox.classList.remove('d-none');
                        } else {
                            createInvoiceButton.disabled = false;
                            alertBox.classList.add('d-none');
                        }
                    } else {
                        alertBox.textContent = data.message;
                        alertBox.classList.remove('d-none');
                        createInvoiceButton.disabled = true;
                        clearProductFields();
                    }
                })
                .catch(() => {
                    alertBox.textContent = '⚠️ Error al obtener la información del producto.';
                    alertBox.classList.remove('d-none');
                    createInvoiceButton.disabled = true;
                    clearProductFields();
                });
        } else {
            clearProductFields();
            createInvoiceButton.disabled = true;
            alertBox.classList.add('d-none');
        }
    }

    function clearProductFields() {
        document.getElementById('product_name').value = '';
        document.getElementById('storage').value = '';
        document.getElementById('battery').value = '';
        document.getElementById('color').value = '';
        document.getElementById('units').value = '';
    }

    function clearFormFields() {
        imeiInput.value = '';
        clearProductFields();
        alertBox.classList.add('d-none');
        createInvoiceButton.disabled = true;
        document.getElementById('client').value = '';
        document.getElementById('document_number').value = '';
        document.getElementById('date').value = '';
        document.getElementById('status').selectedIndex = 0;
    }
});
