function initializeInvoiceModal() {
    const imeiInput = document.getElementById("imei");
    const quantityInput = document.getElementById("quantity");
    const addProductButton = document.getElementById("addProductButton");
    const productListBody = document.getElementById("productListBody");
    const createInvoiceButton = document.getElementById("createInvoiceButton");
    const imeiAlert = document.getElementById("imeiAlert");
    const form = document.querySelector("#addInvoiceModal form");
    const priceInput = document.getElementById("price");

    let productList = [];

    // ✅ Detectar cambios en el IMEI en tiempo real
    imeiInput.addEventListener("input", function () {
        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(fetchProductData, 500);
    });

    // Función para buscar los datos del producto por IMEI
    function fetchProductData() {
        const imei = imeiInput.value.trim();
        if (imei.length < 5) {
            clearFields();
            return;
        }

        console.log(`📡 Buscando IMEI: ${imei}`);

        fetch(`/get_product_by_imei/${imei}?_=${new Date().getTime()}`)
            .then(response => response.json())
            .then(data => {
                console.log("✅ Respuesta del backend:", data);

                if (data.success && data.product) {
                    imeiAlert.classList.add("d-none");

                    // 🚀 Actualizamos los valores en la interfaz
                    document.getElementById("product_name").value = data.product.productname;
                    document.getElementById("storage").value = data.product.storage;
                    document.getElementById("battery").value = data.product.battery;
                    document.getElementById("color").value = data.product.color;
                    document.getElementById("units").value = data.product.units;
                    quantityInput.max = data.product.units;

                    console.log("🎯 Datos actualizados en los inputs.");

                    // 🔹 Forzar a Bootstrap a actualizar el modal
                    setTimeout(() => {
                        $('#addInvoiceModal').modal('handleUpdate');
                    }, 100);
                } else {
                    showAlert("⚠️ Producto no encontrado.");
                    clearFields();
                }
            })
            .catch(error => {
                console.error("❌ Error en fetch:", error);
                showAlert("⚠️ Error al obtener la información del producto.");
                clearFields();
            });
    }

    // Función para agregar producto a la lista
    addProductButton.addEventListener("click", function () {
        const imei = imeiInput.value.trim();
        const product_name = document.getElementById("product_name").value;
        const storage = document.getElementById("storage").value;
        const battery = document.getElementById("battery").value;
        const color = document.getElementById("color").value;
        const units = parseInt(document.getElementById("units").value, 10);
        const quantity = parseInt(quantityInput.value, 10);
        const price = parseFloat(priceInput.value);  // Obtener el precio ingresado

        // 🔍 Validaciones antes de agregar el producto
        if (!imei || !product_name || quantity <= 0 || quantity > units || isNaN(quantity) || isNaN(price) || price <= 0) {
            alert("⚠️ La cantidad o el precio no son válidos.");
            return; // No agregar el producto si hay un error de validación
        }

        // 🛑 Evitar productos duplicados en la lista
        if (productList.some(product => product.imei === imei)) {
            alert("⚠️ Este producto ya está en la tabla.");
            return;
        }

        // 📌 Agregar producto a la lista
        productList.push({ imei, product_name, storage, battery, color, quantity, price });

        // 🔹 Crear fila en la tabla
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${imei}</td>
            <td>${product_name}</td>
            <td>${storage}</td>
            <td>${battery}</td>
            <td>${color}</td>
            <td>${quantity}</td>
            <td>${price}</td>
            <td><button class="btn btn-danger btn-sm delete-btn">❌</button></td>
        `;

        productListBody.appendChild(row);
        updateCreateButton();  // Actualiza el estado del botón de crear factura

        // ✅ Quitar los atributos `required` de los campos IMEI y Cantidad
        imeiInput.removeAttribute("required");
        quantityInput.removeAttribute("required");

        // 🧹 Limpiar campos después de agregar el producto
        clearFields();
    });

    // ❌ Eliminar producto de la tabla
    productListBody.addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-btn")) {
            const row = event.target.closest("tr");
            const imeiToRemove = row.cells[0].innerText;
            productList = productList.filter(p => p.imei !== imeiToRemove);
            row.remove();
            updateCreateButton();
        }
    });

    // ✅ Validar que haya productos antes de enviar el formulario
    form.addEventListener("submit", function (event) {
        const clientName = document.getElementById("client").value.trim();
        const clientDocument = document.getElementById("document_number").value.trim();

        if (productList.length === 0) {
            alert("⚠️ Debes agregar al menos un producto antes de crear la factura.");
            event.preventDefault();
            return;
        }

        if (!clientName || !clientDocument) {
            alert("⚠️ Debes completar los datos del cliente.");
            event.preventDefault();
            return;
        }

        // 🔹 Agregar los productos como un input oculto en el formulario antes de enviarlo
        let productInput = document.getElementById("product_data");
        if (!productInput) {
            productInput = document.createElement("input");
            productInput.type = "hidden";
            productInput.name = "products";
            productInput.id = "product_data";
            form.appendChild(productInput);
        }
        productInput.value = JSON.stringify(productList);
    });

    // 🔹 Habilitar o deshabilitar el botón "Crear Factura"
    function updateCreateButton() {
        createInvoiceButton.disabled = productList.length === 0;
    }

    // 🔄 Limpiar los campos después de agregar un producto
    function clearFields() {
        imeiInput.value = "";
        document.getElementById("product_name").value = "";
        document.getElementById("storage").value = "";
        document.getElementById("battery").value = "";
        document.getElementById("color").value = "";
        document.getElementById("units").value = "";
        quantityInput.value = "";
        priceInput.value = "";  // Limpiar también el campo de precio
    }

    // ⚠️ Mostrar alerta de error
    function showAlert(message) {
        imeiAlert.textContent = message;
        imeiAlert.classList.remove("d-none");
    }

    // ✅ Ocultar alerta
    function hideAlert() {
        imeiAlert.classList.add("d-none");
    }

    // 🚀 Forzar Bootstrap a redibujar el modal cuando se abra
    document.getElementById("addInvoiceModal").addEventListener("shown.bs.modal", function () {
        $('#addInvoiceModal').modal('handleUpdate');
    });

    // Prevenir que el formulario se envíe al presionar Enter
    imeiInput.addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
        }
    });

    quantityInput.addEventListener("keydown", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
        }
    });
}

// 🚀 Inicializar el modal cuando se abra
document.addEventListener("DOMContentLoaded", function () {
    const addInvoiceModal = document.getElementById("addInvoiceModal");

    addInvoiceModal.addEventListener("show.bs.modal", function () {
        initializeInvoiceModal();
    });
});

