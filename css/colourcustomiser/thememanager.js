/* --- 1. THE BRAINS: Text Contrast Helper --- */
function getContrastColor(hex) {
    if (!hex) return '#ffffff';
    const r = parseInt(hex.replace('#', '').substr(0, 2), 16);
    const g = parseInt(hex.replace('#', '').substr(2, 2), 16);
    const b = parseInt(hex.replace('#', '').substr(4, 2), 16);
    return ((r * 299 + g * 587 + b * 114) / 1000) >= 150 ? '#000000' : '#ffffff';
}

/* --- 2. THE NUCLEAR OPTION: Syncs Every Single Button --- */
function applyTheme(navbar, bodyBg) {
    const root = document.documentElement;
    const navText = getContrastColor(navbar);

    // Set Global Variables
    root.style.setProperty('--navbar-color', navbar);
    root.style.setProperty('--navbar-text', navText);
    root.style.setProperty('--body-bg', bodyBg);

    // FORCE sync all buttons (Change, Edit, Submit, Hobbies)
    const themeElements = document.querySelectorAll('.footer, footer, .navbar, nav, .btn-submit-large, .btn-brown, .interest-tag.selected, .btn-save, .btn-add-big, .btn-upload, .btn-customize');
    themeElements.forEach(el => {
        el.style.setProperty('background-color', navbar, 'important');
        el.style.setProperty('color', navText, 'important');
    });

    // Save so it survives a refresh
    localStorage.setItem('bridgegen-theme', JSON.stringify({ navbar, bodyBg }));
}

/* --- 3. THE PICKERS: Won't crash if LocalStorage is empty --- */
function setNav(element, hex) {
    const saved = JSON.parse(localStorage.getItem('bridgegen-theme')) || { bodyBg: '#f4f7f6' };
    applyTheme(hex, saved.bodyBg);
}

function setBg(element, hex) {
    const saved = JSON.parse(localStorage.getItem('bridgegen-theme')) || { navbar: '#4A90E2' };
    applyTheme(saved.navbar, hex);
}

function applyPreset(navColor, bodyBg) {
    applyTheme(navColor, bodyBg);
}

/* --- 4. THE UI CONTROLS: Modal & Tabs --- */
function openColorModal() {
    const m = document.getElementById('colorModal');
    if (m) m.style.display = 'flex';
}

function closeColorModal() {
    const m = document.getElementById('colorModal');
    if (m) m.style.display = 'none';
}

function switchTab(tabId) {
    const custom = document.getElementById('tab-custom');
    const suggested = document.getElementById('tab-suggested');
    
    if (custom && suggested) {
        custom.style.display = (tabId === 'custom') ? 'block' : 'none';
        suggested.style.display = (tabId === 'suggested') ? 'block' : 'none';
    }

    // Fixes the active green underline
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    if (event && event.currentTarget) event.currentTarget.classList.add('active');
}

/* --- 5. INITIAL LOAD: Runs when page opens --- */
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('bridgegen-theme');
    if (saved) {
        const theme = JSON.parse(saved);
        applyTheme(theme.navbar, theme.bodyBg);
    }
});

function resetDefaults() {
    // 1. Define your original "BridgeGen" blue theme
    const originalNav = '#4A90E2'; 
    const originalBg = '#f4f6f8';
    const originalText = '#ffffff';

    // 2. Wipe the browser's memory so it doesn't reload the "broken" theme
    localStorage.removeItem('bridgegen-theme');

    // 3. Manually push the original colors back to the page
    const root = document.documentElement;
    root.style.setProperty('--navbar-color', originalNav);
    root.style.setProperty('--body-bg', originalBg);
    root.style.setProperty('--navbar-text', originalText);

    // 4. Force every button and the footer to turn back to blue immediately
    const themeElements = document.querySelectorAll('.footer, footer, .navbar, nav, .btn-submit-large, .btn-brown, .interest-tag.selected, .btn-save, .btn-add-big, .btn-upload, .btn-customize');
    themeElements.forEach(el => {
        el.style.setProperty('background-color', originalNav, 'important');
        el.style.setProperty('color', originalText, 'important');
    });

    console.log("BridgeGen Reset Successful!");
}