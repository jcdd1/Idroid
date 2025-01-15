document.addEventListener('DOMContentLoaded', function () {
    const editProductModal = document.getElementById('editProductModal');
    editProductModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget; // Botón que disparó el modal
        const productData = button.getAttribute('data-product'); // Datos JSON

        if (!productData) {
            console.error("No se encontraron datos para el producto.");
            return;
        }

        const product = JSON.parse(productData);

        // Asigna valores a los campos del modal
        document.getElementById('edit_product_id').value = product.product_id || "";
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
        document.getElementById('edit_acquisition_date').value = product.acquisition_date || "";
    });
});
