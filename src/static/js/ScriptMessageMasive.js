document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    
    fetch('/carga_masiva', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())  // Ahora siempre esperamos un JSON
    .then(data => {
        if (data.error) {
            alert(data.error);  // Muestra el error si existe
        } else {
            alert(data.message);  // Muestra el mensaje de éxito
        }
    })
    .catch(error => console.error('Error:', error));
});