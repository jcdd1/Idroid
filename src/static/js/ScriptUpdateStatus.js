document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.btn-update-status');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const imei = this.getAttribute('data-imei');
            const status = this.getAttribute('data-status');

            fetch(`/update_status/${imei}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify({ status: status })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error al actualizar el estado: ' + data.message);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});