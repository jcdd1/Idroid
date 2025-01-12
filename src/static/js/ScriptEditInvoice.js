document.addEventListener("DOMContentLoaded", () => {
    
    const editInvoiceModal = document.getElementById("editInvoiceModal");
    const editButtons = document.querySelectorAll("button[data-bs-target='#editInvoiceModal']");

    
    editButtons.forEach(button => {
        button.addEventListener("click", () => {
            // Obtener los datos de la factura desde el atributo data-invoice
            const invoiceData = JSON.parse(button.getAttribute("data-invoice"));

            // Llenar los campos del modal con los datos de la factura
            document.getElementById("invoice_id").value = invoiceData.invoice_id || "";
            document.getElementById("type").value = invoiceData.type || "";
            document.getElementById("document_number").value = invoiceData.document_number || "";
            document.getElementById("date").value = invoiceData.date ? formatDateTime(invoiceData.date) : "";
            document.getElementById("client").value = invoiceData.client || "";
            document.getElementById("status").value = invoiceData.status || "Pending";
        });
    });

    /**
     * Función para formatear una fecha y hora en formato "YYYY-MM-DDTHH:mm".
     * @param {string} dateTimeString 
     * @returns {string} 
     */
    function formatDateTime(dateTimeString) {
        const date = new Date(dateTimeString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const hours = String(date.getHours()).padStart(2, "0");
        const minutes = String(date.getMinutes()).padStart(2, "0");
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
});
