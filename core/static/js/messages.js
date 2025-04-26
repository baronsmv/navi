document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 4000);  // Se cierra a los 4 segundos
});
