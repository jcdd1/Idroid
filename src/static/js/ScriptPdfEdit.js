// PDF Edit functionality
document.addEventListener('DOMContentLoaded', function() {
    // Intercept PDF download links
    document.querySelectorAll('a[href^="/download_invoice/"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Extract invoice ID from the href
            const href = this.getAttribute('href');
            const invoiceId = href.split('/').pop();
            
            // Store the invoice ID for later use
            document.getElementById('editPdfInvoiceId').value = invoiceId;
            
            // Show the confirmation modal
            const confirmModal = new bootstrap.Modal(document.getElementById('confirmEditPdfModal'));
            confirmModal.show();
        });
    });
    
    // Handle "No" button click - proceed with normal PDF download
    document.getElementById('noPdfEdit').addEventListener('click', function() {
        const invoiceId = document.getElementById('editPdfInvoiceId').value;
        window.location.href = `/download_invoice/${invoiceId}`;
        
        // Hide the confirmation modal
        bootstrap.Modal.getInstance(document.getElementById('confirmEditPdfModal')).hide();
    });
    
    // Handle "Yes" button click - open edit modal
    document.getElementById('yesPdfEdit').addEventListener('click', function() {
        // Hide the confirmation modal
        bootstrap.Modal.getInstance(document.getElementById('confirmEditPdfModal')).hide();
        
        // Show the edit modal
        const editModal = new bootstrap.Modal(document.getElementById('editPdfModal'));
        editModal.show();
    });
    
    // Handle generate edited PDF button click
    document.getElementById('generateEditedPdf').addEventListener('click', function() {
        const invoiceId = document.getElementById('editPdfInvoiceId').value;
        
        // Get the edited values
        const headerData = [
            document.getElementById('pdfHeader1').value,
            document.getElementById('pdfHeader2').value,
            document.getElementById('pdfHeader3').value,
            document.getElementById('pdfHeader4').value,
            document.getElementById('pdfHeader5').value
        ];
        
        const warrantyText = document.getElementById('pdfWarranty').value;
        const legalText = document.getElementById('pdfLegal').value;
        
        // Prepare data for the server
        const editData = {
            header_lines: headerData,
            warranty_text: warrantyText,
            legal_text: legalText
        };
        
        // Create a form to send the data
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/download_invoice/${invoiceId}`;
        form.style.display = 'none';
        
        // Add CSRF token if you're using Flask-WTF
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        csrfInput.value = csrfToken;
        form.appendChild(csrfInput);
        
        // Add the edit data as JSON
        const dataInput = document.createElement('input');
        dataInput.type = 'hidden';
        dataInput.name = 'edit_data';
        dataInput.value = JSON.stringify(editData);
        form.appendChild(dataInput);
        
        // Submit the form
        document.body.appendChild(form);
        form.submit();
        
        // Hide the edit modal
        bootstrap.Modal.getInstance(document.getElementById('editPdfModal')).hide();
    });
});