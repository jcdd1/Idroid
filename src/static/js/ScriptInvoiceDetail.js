document.addEventListener("DOMContentLoaded", function() {
    var invoiceDetailModal = document.getElementById("invoiceDetailModal");

    invoiceDetailModal.addEventListener("show.bs.modal", function(event) {
        var button = event.relatedTarget;
        var invoiceId = button.getAttribute("data-invoice-id");

        fetch(`/get_invoice_details/${invoiceId}`)
            .then(response => response.json())
            .then(data => {
                var tbody = document.getElementById("invoiceDetailBody");
                tbody.innerHTML = ""; // Limpiar contenido previo
                
                if (data.length === 0 || data.message) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay detalles disponibles.</td></tr>';
                    return;
                }

                data.forEach(item => {
                    var row = `<tr>
                        <td>${item.product_name}</td>
                        <td class="text-center">${item.quantity}</td>
                        <td class="text-center">$${item.price.toFixed(2)}</td>
                        <td class="text-center">$${(item.quantity * item.price).toFixed(2)}</td>
                    </tr>`;
                    tbody.innerHTML += row;
                });
            })
            .catch(error => console.error("Error al obtener los detalles:", error));
    });
});
