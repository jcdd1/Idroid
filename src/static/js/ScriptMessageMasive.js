document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    fetch('/carga_masiva', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const modalMessage = document.getElementById('modalMessage');
        modalMessage.textContent = data.message;
        const modalElement = new bootstrap.Modal(document.getElementById('resultModal'));
        modalElement.show();
    })
    .catch(error => console.error('Error:', error));
});