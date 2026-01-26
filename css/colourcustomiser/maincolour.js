document.addEventListener('DOMContentLoaded', () => {
    // Check if the modal exists before adding logic
    const modal = document.getElementById('colorModal');
    if (!modal) return;

    // Default to the first tab
    switchTab('custom');
});

// Function to Open the Modal
function openColorModal() {
    document.getElementById('colorModal').style.display = "flex";
}

// Function to Close the Modal
function closeColorModal() {
    document.getElementById('colorModal').style.display = "none";
}

// Function to Switch Tabs (Website Colour vs Suggested Themes)
function switchTab(tabName) {
    // 1. Hide all tab content
    document.getElementById('tab-custom').style.display = "none";
    document.getElementById('tab-suggested').style.display = "none";
    
    // 2. Remove 'active' class from all buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // 3. Show the selected tab and activate button
    if(tabName === 'custom') {
        document.getElementById('tab-custom').style.display = "block";
        buttons[0].classList.add('active'); // First button (Website Colour)
    } else {
        document.getElementById('tab-suggested').style.display = "grid"; // Grid for cards
        buttons[1].classList.add('active'); // Second button (Suggested)
    }
}

// Close modal if user clicks outside the box
window.onclick = function(event) {
    const modal = document.getElementById('colorModal');
    if (event.target == modal) {
        closeColorModal();
    }
}