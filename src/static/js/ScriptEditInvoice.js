document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".editInvoiceBtn").forEach(button => {
        button.addEventListener("click", async function () {
            const invoiceId = this.dataset.id;
            document.getElementById("edit_invoice_id").value = invoiceId;

            // Obtener datos de la factura
            const response = await fetch(`/get_invoice_details/${invoiceId}`);
            const data = await response.json();

            document.getElementById("edit_type").value = data.type;
            document.getElementById("edit_date").value = data.date;
            document.getElementById("edit_status").value = data.status;

            // Cargar productos
            const productListBody = document.getElementById("edit_productListBody");
            productListBody.innerHTML = "";

            data.products.forEach(product => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${product.imei}</td>
                    <td>${product.name}</td>
                    <td>${product.storage}</td>
                    <td>${product.battery}</td>
                    <td>${product.color}</td>
                    <td>${product.quantity}</td>
                    <td><button class="btn btn-danger btn-sm delete-btn" data-imei="${product.imei}">❌</button></td>
                `;
                productListBody.appendChild(row);
            });

            // Eliminar productos
            document.querySelectorAll(".delete-btn").forEach(btn => {
                btn.addEventListener("click", function () {
                    this.closest("tr").remove();
                });
            });
        });
    });

    // Confirmar eliminación de factura
    document.querySelectorAll(".deleteInvoiceBtn").forEach(button => {
        button.addEventListener("click", function () {
            const invoiceId = this.dataset.id;
            if (confirm("¿Seguro que deseas eliminar esta factura?")) {
                fetch(`/delete_invoice/${invoiceId}`, { method: "POST" })
                .then(response => response.json())
                .then(() => location.reload());
            }
        });
    });
});
