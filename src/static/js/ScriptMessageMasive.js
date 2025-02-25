document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    fetch('/carga_masiva', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error en la carga: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('modalMessage').textContent = data.message;
        new bootstrap.Modal(document.getElementById('resultModal')).show();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Hubo un error en la carga. Revisa la consola para más detalles.');
    });
});