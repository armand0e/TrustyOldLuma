/**
 * Theme management for Luna Gaming Tool
 */

document.addEventListener('DOMContentLoaded', async () => {
  const themeSwitch = document.getElementById('theme-switch');
  
  // Get theme preference from Electron store
  const isDarkMode = await window.electron.theme.getDarkMode();
  
  // Apply theme
  setTheme(isDarkMode);
  
  // Update switch state
  themeSwitch.checked = isDarkMode;
  
  // Listen for theme changes
  themeSwitch.addEventListener('change', async (e) => {
    const isDark = e.target.checked;
    await window.electron.theme.setDarkMode(isDark);
    setTheme(isDark);
  });
});

/**
 * Set theme based on dark mode preference
 * @param {boolean} isDark - Whether to use dark theme
 */
function setTheme(isDark) {
  if (isDark) {
    document.body.classList.add('dark-theme');
  } else {
    document.body.classList.remove('dark-theme');
  }
}