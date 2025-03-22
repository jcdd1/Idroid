document.addEventListener("DOMContentLoaded", function() {
    var invoiceDetailModal = document.getElementById("invoiceDetailModal");

    invoiceDetailModal.addEventListener("show.bs.modal", function(event) {
        var button = event.relatedTarget;
        var invoiceId = button.getAttribute("data-invoice-id");

        fetch(`/get_invoice_details/${invoiceId}`)
            .then(response => response.json())
            .then(data => {
                var tbody = document.getElementById("invoiceDetailBody");
                var totalElement = document.getElementById("invoiceTotal");
                tbody.innerHTML = ""; // Limpiar contenido previo
                let totalAmount = 0;

                if (data.length === 0 || data.message) {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay detalles disponibles.</td></tr>';
                    totalElement.textContent = "$0.00"; // Mostrar total 0 si no hay detalles
                    return;
                }

                data.forEach(item => {
                    var subtotal = item.quantity * item.price;
                    totalAmount += subtotal; // Sumar al total

                    var row = `<tr>
                        <td>${item.imei}</td>
                        <td>${item.product_name}</td>
                        <td class="text-center">${item.quantity}</td>
                        <td class="text-center">$${item.price.toFixed(2)}</td>
                        <td class="text-center">$${subtotal.toFixed(2)}</td>
                    </tr>`;
                    tbody.innerHTML += row;
                });

                // Mostrar el total en el modal
                totalElement.textContent = `$${totalAmount.toFixed(2)}`;
            })
            .catch(error => console.error("Error al obtener los detalles:", error));
    });
});
