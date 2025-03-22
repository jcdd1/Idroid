document.addEventListener("DOMContentLoaded", function () {
    // Evento para el botón de Editar
    document.querySelectorAll(".editProductBtn").forEach(button => {
        button.addEventListener("click", async function () {
            const productId = this.dataset.id;
            document.getElementById("edit_product_id").value = productId;

            // Obtener datos del producto
            const response = await fetch(`/get_product_details/${productId}`);
            const data = await response.json();

            document.getElementById("edit_product_name").value = data.name;
            document.getElementById("edit_product_memory").value = data.memory;
            document.getElementById("edit_product_battery").value = data.battery;
            document.getElementById("edit_product_color").value = data.color;
            document.getElementById("edit_product_quantity").value = data.quantity;
            document.getElementById("edit_product_price").value = data.price;

            // Cargar productos en la tabla
            const productListBody = document.getElementById("edit_productListBody");
            productListBody.innerHTML = "";

            data.products.forEach(product => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${product.imei}</td>
                    <td>${product.name}</td>
                    <td>${product.memory}</td>
                    <td>${product.battery}</td>
                    <td>${product.color}</td>
                    <td>${product.quantity}</td>
                    <td>${product.price}</td>
                    <td>
                        <!-- Botón Eliminar -->
                        <button class="btn btn-danger btn-sm deleteProductBtn" data-imei="${product.imei}">❌ Eliminar</button>
                    </td>
                `;
                productListBody.appendChild(row);
            });

            // Eliminar productos
            document.querySelectorAll(".deleteProductBtn").forEach(btn => {
                btn.addEventListener("click", function () {
                    this.closest("tr").remove();
                });
            });
        });
    });

    // Confirmar eliminación de producto
    document.querySelectorAll(".deleteProductBtn").forEach(button => {
        button.addEventListener("click", function () {
            const productId = this.dataset.imei;
            if (confirm("¿Seguro que deseas eliminar este producto?")) {
                fetch(`/delete_product/${productId}`, { method: "POST" })
                .then(response => response.json())
                .then(() => location.reload());
            }
        });
    });
});
