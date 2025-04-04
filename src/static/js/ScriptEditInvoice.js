document.addEventListener("DOMContentLoaded", function () {
    const imeiInput = document.getElementById("update_imei");
    const quantityInput = document.getElementById("update_quantity");
    const addProductButton = document.getElementById("update_addProductButton");
    const productListBody = document.getElementById("update_productListBody");
    const priceInput = document.getElementById("update_price");
    const imeiAlert = document.getElementById("update_imeiAlert");

    let productList = [];

    // Función para cargar los productos asociados a la factura
    function initializeUpdateInvoiceModal(products) {
        productList = products;

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
                    document.getElementById("update_product_name").value = data.product.productname;
                    document.getElementById("update_storage").value = data.product.storage;
                    document.getElementById("update_battery").value = data.product.battery;
                    document.getElementById("update_color").value = data.product.color;
                    document.getElementById("update_units").value = data.product.units;
                    quantityInput.max = data.product.units;
                } else {
                    showAlert("⚠️ Producto no encontrado.");
                    clearFields();
                }
            })
            .catch(() => {
                showAlert("⚠️ Error al obtener la información del producto.");
                clearFields();
            });
    }

    imeiInput.addEventListener("input", function () {
        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(fetchProductData, 500);
    });

    addProductButton.addEventListener("click", function () {
        const imei = imeiInput.value.trim();
        const product_name = document.getElementById("update_product_name").value;
        const storage = document.getElementById("update_storage").value;
        const battery = document.getElementById("update_battery").value;
        const color = document.getElementById("update_color").value;
        const units = parseInt(document.getElementById("update_units").value, 10);
        const quantity = parseInt(quantityInput.value, 10);
        const price = parseFloat(priceInput.value);

        if (!imei || !product_name || quantity <= 0 || quantity > units || isNaN(quantity) || isNaN(price) || price <= 0) {
            alert("⚠️ La cantidad o el precio no son válidos.");
            return;
        }

        if (productList.some(product => product.imei === imei)) {
            alert("⚠️ Este producto ya está en la tabla.");
            return;
        }

        productList.push({ imei, product_name, storage, battery, color, quantity, price });

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

        clearFields();
    });

    productListBody.addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-btn")) {
            const row = event.target.closest("tr");
            const imeiToRemove = row.cells[0].innerText;
            productList = productList.filter(p => p.imei !== imeiToRemove);
            row.remove();
        }
    });

    function showAlert(message) {
        imeiAlert.textContent = message;
        imeiAlert.classList.remove("d-none");
    }

    function clearFields() {
        imeiInput.value = "";
        document.getElementById("update_product_name").value = "";
        document.getElementById("update_storage").value = "";
        document.getElementById("update_battery").value = "";
        document.getElementById("update_color").value = "";
        document.getElementById("update_units").value = "";
        quantityInput.value = "";
        priceInput.value = "";
    }

    // Exponer la función globalmente si se necesita usar desde otros scripts
    window.initializeUpdateInvoiceModal = initializeUpdateInvoiceModal;
});
