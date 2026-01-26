document.addEventListener("DOMContentLoaded", function() {
    // Simulating a notification check
    // In a real app, this would use fetch() to ask Python for the count
    const badge = document.getElementById('notif-badge');
    if (badge) {
        // Toggle badge visibility based on logic
        badge.style.display = 'block'; 
    }
});