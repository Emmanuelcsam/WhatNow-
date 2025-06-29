// Location Button Fix
// Add this to the main.js file to ensure the location button works properly

// Ensure the button click properly triggers location detection
if (getLocationBtn) {
    // Remove any existing listeners first
    const newBtn = getLocationBtn.cloneNode(true);
    getLocationBtn.parentNode.replaceChild(newBtn, getLocationBtn);
    
    // Add new click handler
    newBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        console.log('Location button clicked - starting detection');
        
        // Visual feedback
        this.disabled = true;
        const originalText = this.textContent;
        this.textContent = 'Detecting...';
        
        try {
            // Call the location detection function
            const location = await getCurrentLocation();
            console.log('Location detected:', location);
            
            // Success - the function handles UI updates
        } catch (error) {
            console.error('Location detection error:', error);
            
            // Reset button on error
            this.disabled = false;
            this.textContent = originalText;
            
            // Show error message
            if (locationMessage) {
                locationMessage.innerHTML = '<div class="text-danger">Failed to detect location. Please try again.</div>';
            }
        }
    });
    
    console.log('Location button fix applied');
}