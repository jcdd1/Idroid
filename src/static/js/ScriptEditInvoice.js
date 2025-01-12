document.addEventListener("DOMContentLoaded", () => {
    const editButtons = document.querySelectorAll(".btn-edit");
    const modal = document.getElementById("editInvoiceModal");

    editButtons.forEach(button => {
        button.addEventListener("click", () => {
            const invoice = JSON.parse(button.getAttribute("data-invoice"));
            modal.querySelector("#invoice_id").value = invoice.id;
            modal.querySelector("#type").value = invoice.type;
            modal.querySelector("#document_number").value = invoice.document_number;
            modal.querySelector("#date").value = invoice.date;
            modal.querySelector("#client").value = invoice.client;
        });
    });
});
