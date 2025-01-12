document.addEventListener('DOMContentLoaded', function () {
    const editProductModal = document.getElementById('editProductModal');
    editProductModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget; // Botón que disparó el modal
        const productData = button.getAttribute('data-product'); // Datos JSON

        // Verifica si el producto está presente en el atributo
        if (!productData) {
            console.error("No se encontraron datos para el producto.");
            return;
        }

        const product = JSON.parse(productData); // Convertir JSON string a objeto

        // Rellenar los campos del modal con los datos del producto
        document.getElementById('product_id').value = product.product_id || "";
        document.getElementById('productname').value = product.productname || "";
        document.getElementById('imei').value = product.imei || "";
        document.getElementById('storage').value = product.storage || "";
        document.getElementById('battery').value = product.battery || "";
        document.getElementById('color').value = product.color || "";
        document.getElementById('description').value = product.description || "";
        document.getElementById('cost').value = product.cost || "";
        document.getElementById('current_status').value = product.current_status || "";
        document.getElementById('acquisition_date').value = product.acquisition_date || "";
        document.getElementById('warehouse_name').value = product.warehouse_name || "";
        document.getElementById('document_number').value = product.document_number || "";
    });
});

