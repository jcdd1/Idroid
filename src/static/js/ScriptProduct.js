document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ ScriptProduct.js cargado correctamente.");

    document.querySelectorAll(".delete-product-btn").forEach(button => {
        button.addEventListener("click", function () {
            let productId = this.getAttribute("data-product-id");

            if (!productId || isNaN(productId)) {
                console.error("❌ Error: ID del producto no válido.", productId);
                alert("❌ Error: ID del producto no válido.");
                return;
            }

            if (confirm(`⚠️ ¿Estás seguro de que quieres eliminar el producto con ID ${productId}? Esta acción no se puede deshacer.`)) {
                console.log(`📤 Enviando solicitud para eliminar producto con ID: ${productId}`);

                fetch(`/delete_product/${productId}`, { 
                    method: "POST",  
                    headers: { 
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    credentials: "include" // ✅ Permite enviar cookies de sesión
                })
                .then(response => response.json())
                .then(data => {
                    console.log("📥 Respuesta del servidor:", data);

                    if (data.success) {
                        alert("✅ Producto eliminado correctamente.");

                        // 🗑️ Eliminar la fila de la tabla sin recargar la página
                        let row = document.querySelector(`button[data-product-id='${productId}']`).closest("tr");
                        if (row) row.remove();
                    } else {
                        alert(`❌ Error al eliminar producto: ${data.message}`);
                    }
                })
                .catch(error => console.error("❌ Error en la solicitud:", error));
            }
        });
    });
});
