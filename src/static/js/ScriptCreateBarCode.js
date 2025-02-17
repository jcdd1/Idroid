document.addEventListener("DOMContentLoaded", function() {
    // Seleccionar todos los botones con la clase "generate-barcode"
    document.querySelectorAll(".generate-barcode").forEach(button => {
        button.addEventListener("click", function() {
            let productId = this.getAttribute("data-product-id"); // Obtener el IMEI del producto
            console.log(productId)
            fetch(`/generate_barcode/${productId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Error al generar el código de barras.");
                    }
                    return response.blob();
                })
                .then(blob => {
                    let url = window.URL.createObjectURL(blob);
                    let a = document.createElement("a");
                    a.href = url;
                    a.download = `${productId}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                })
                .catch(error => {
                    alert(error.message);
                });
        });
    });
});
