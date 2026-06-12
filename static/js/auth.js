document.addEventListener("DOMContentLoaded", () => {
    // Solo validamos el registro en el Frontend
    const registroForm = document.getElementById("registroForm");
    
    if (registroForm) {
        registroForm.addEventListener("submit", (e) => {
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirm_password").value;

            // Si las contraseñas no coinciden, detenemos el envío del formulario
            if (password !== confirmPassword) {
                e.preventDefault(); // Detiene el envío a Django
                alert("Las contraseñas no coinciden. Por favor, verifica.");
            }
        });
    }
});

window.togglePasswordVisibility = function (inputId, eyeId) {
    const input = document.getElementById(inputId);
    const eye = document.getElementById(eyeId);

    if (!input || !eye) {
        return;
    }

    if (input.type === "password") {
        input.type = "text";
        eye.textContent = "🙈";
    } else {
        input.type = "password";
        eye.textContent = "👁️";
    }
};