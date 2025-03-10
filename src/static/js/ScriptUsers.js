document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ ScriptUsers.js cargado correctamente.");

    // 📌 Capturar evento cuando se presiona el botón "Editar Usuario"
    document.querySelectorAll(".edit-user-btn").forEach(button => {
        button.addEventListener("click", function () {
            // Obtener el atributo data-user
            const userDataString = this.getAttribute("data-user");

            console.log("🔍 Datos recibidos en botón de edición:", userDataString); // Verificar en consola

            try {
                const userData = JSON.parse(userDataString); // Convertir de JSON a objeto

                console.log("✅ Usuario cargado en el modal:", userData);

                // Llenar los campos del formulario de edición
                document.getElementById("edit_user_id").value = userData.user_id || "";
                document.getElementById("edit_name").value = userData.name || "";

                // Seleccionar el rol correcto en el desplegable
                const roleSelect = document.getElementById("edit_role");
                roleSelect.value = userData.role || "usuario"; // Si no hay rol, selecciona "usuario"

                // Seleccionar la bodega correcta en el desplegable
                const warehouseSelect = document.getElementById("edit_warehouse_id");
                warehouseSelect.value = userData.warehouse_id || "";

                document.getElementById("edit_username").value = userData.username || "";

            } catch (error) {
                console.error("❌ Error al parsear JSON:", error);
            }
        });
    });

    // 📌 Capturar evento cuando se presiona el botón "Eliminar Usuario"
    document.querySelectorAll(".delete-user-btn").forEach(button => {
        button.addEventListener("click", function () {
            const userId = this.getAttribute("data-user-id");

            if (!userId) {
                alert("❌ Error: No se encontró el ID del usuario.");
                return;
            }

            if (confirm("⚠️ ¿Estás seguro de que quieres eliminar este usuario? Esta acción no se puede deshacer.")) {
                fetch(`/delete_user/${userId}`, { 
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": document.querySelector("input[name='csrf_token']").value
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert("✅ Usuario eliminado correctamente.");
                        location.reload(); // Recargar la página para actualizar la lista
                    } else {
                        alert(`❌ Error al eliminar usuario: ${data.message}`);
                    }
                })
                .catch(error => console.error("❌ Error en la solicitud:", error));
            }
        });
    });

    // 📌 Validación en el formulario de edición antes de enviar
    document.getElementById("editUserForm")?.addEventListener("submit", function (event) {
        const name = document.getElementById("edit_name").value.trim();
        const username = document.getElementById("edit_username").value.trim();

        if (!name || !username) {
            event.preventDefault();
            alert("⚠️ El nombre y el usuario son obligatorios.");
        }
    });
});
