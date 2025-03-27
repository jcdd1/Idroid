document.addEventListener("DOMContentLoaded", function () {
    const imeiInput = document.getElementById("imei");
    const quantityInput = document.getElementById("quantity");
    const addProductButton = document.getElementById("addProductButton");
    const productListBody = document.getElementById("edit_productListBody");
    const priceInput = document.getElementById("price");
    const imeiAlert = document.getElementById("imeiAlert");

    let productList = [];

    // Función para cargar los productos asociados a la factura
    function initializeEditInvoiceModal(products) {
        productList = products; // Guardamos los productos en el arreglo 'productList'

        // Rellenamos la tabla con los productos asociados
        products.forEach(product => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${product.imei}</td>
                <td>${product.product_name}</td>
                <td>${product.storage}</td>
                <td>${product.battery}</td>
                <td>${product.color}</td>
                <td>${product.quantity}</td>
                <td>${product.price}</td>
                <td><button class="btn btn-danger btn-sm delete-btn">❌</button></td>
            `;
            productListBody.appendChild(row);
        });
    }

    // Cargar los datos del producto al seleccionar el IMEI
    function fetchProductData() {
        const imei = imeiInput.value.trim();
        if (imei.length < 5) {
            clearFields();
            return;
        }

        fetch(`/get_product_by_imei/${imei}?_=${new Date().getTime()}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.product) {
                    imeiAlert.classList.add("d-none");

                    // Rellenar los campos con la información del producto
                    document.getElementById("product_name").value = data.product.productname;
                    document.getElementById("storage").value = data.product.storage;
                    document.getElementById("battery").value = data.product.battery;
                    document.getElementById("color").value = data.product.color;
                    document.getElementById("units").value = data.product.units;
                    quantityInput.max = data.product.units;
                } else {
                    showAlert("⚠️ Producto no encontrado.");
                    clearFields();
                }
            })
            .catch(error => {
                showAlert("⚠️ Error al obtener la información del producto.");
                clearFields();
            });
    }

    // Detectar cambios en el IMEI en tiempo real
    imeiInput.addEventListener("input", function () {
        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(fetchProductData, 500);
    });

    // Agregar el producto a la lista
    addProductButton.addEventListener("click", function () {
        const imei = imeiInput.value.trim();
        const product_name = document.getElementById("product_name").value;
        const storage = document.getElementById("storage").value;
        const battery = document.getElementById("battery").value;
        const color = document.getElementById("color").value;
        const units = parseInt(document.getElementById("units").value, 10);
        const quantity = parseInt(quantityInput.value, 10);
        const price = parseFloat(priceInput.value);

        // Validaciones antes de agregar el producto
        if (!imei || !product_name || quantity <= 0 || quantity > units || isNaN(quantity) || isNaN(price) || price <= 0) {
            alert("⚠️ La cantidad o el precio no son válidos.");
            return;
        }

        // Evitar productos duplicados en la lista
        if (productList.some(product => product.imei === imei)) {
            alert("⚠️ Este producto ya está en la tabla.");
            return;
        }

        // Agregar producto a la lista
        productList.push({ imei, product_name, storage, battery, color, quantity, price });

        // Crear fila en la tabla
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

        // Limpiar los campos después de agregar el producto
        clearFields();
    });

    // Eliminar producto de la tabla
    productListBody.addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-btn")) {
            const row = event.target.closest("tr");
            const imeiToRemove = row.cells[0].innerText;
            productList = productList.filter(p => p.imei !== imeiToRemove);
            row.remove();
        }
    });

    // Mostrar alerta de error
    function showAlert(message) {
        imeiAlert.textContent = message;
        imeiAlert.classList.remove("d-none");
    }

    // Limpiar los campos después de agregar un producto
    function clearFields() {
        imeiInput.value = "";
        document.getElementById("product_name").value = "";
        document.getElementById("storage").value = "";
        document.getElementById("battery").value = "";
        document.getElementById("color").value = "";
        document.getElementById("units").value = "";
        quantityInput.value = "";
        priceInput.value = "";
    }
    


});
