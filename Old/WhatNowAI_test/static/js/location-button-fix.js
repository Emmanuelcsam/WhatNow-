// Location Button Fix - Add this after main.js loads
console.log('Location button fix loading...');

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixLocationButton);
} else {
    fixLocationButton();
}

function fixLocationButton() {
    console.log('Applying location button fix...');
    
    // Check every 500ms for the button to appear
    const checkInterval = setInterval(() => {
        const button = document.getElementById('get-location-btn');
        const step4 = document.getElementById('step-4');
        
        // Only setup if button exists and step 4 is visible
        if (button && step4 && !step4.classList.contains('d-none')) {
            console.log('Location button found and step 4 is visible!');
            clearInterval(checkInterval);
            
            // Remove all existing event listeners
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add a simple click handler
            newButton.onclick = async function(e) {
                e.preventDefault();
                console.log('Location button clicked via onclick!');
                
                // Visual feedback
                this.disabled = true;
                this.textContent = 'Detecting...';
                this.style.opacity = '0.7';
                
                try {
                    // Call getCurrentLocation if it exists
                    if (typeof getCurrentLocation === 'function') {
                        await getCurrentLocation();
                    } else {
                        console.error('getCurrentLocation function not found!');
                        
                        // Fallback: directly call the API
                        const response = await fetch('/api/location/comprehensive', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({})
                        });
                        
                        const data = await response.json();
                        console.log('Location data:', data);
                        
                        if (data.primary_location) {
                            // Update UI
                            const message = document.getElementById('location-message');
                            if (message) {
                                message.innerHTML = `<div class="text-success">Location found: ${data.primary_location.city}, ${data.primary_location.state}</div>`;
                            }
                            
                            // Store location
                            window.userLocation = data.primary_location;
                            
                            // Auto-proceed
                            setTimeout(() => {
                                if (typeof startProcessing === 'function') {
                                    startProcessing();
                                }
                            }, 1500);
                        }
                    }
                } catch (error) {
                    console.error('Location detection error:', error);
                    this.disabled = false;
                    this.textContent = 'Try Again';
                    this.style.opacity = '1';
                }
            };
            
            // Also add addEventListener as backup
            newButton.addEventListener('click', function(e) {
                console.log('Location button clicked via addEventListener!');
            });
            
            // Ensure button is interactive
            newButton.style.cursor = 'pointer';
            newButton.style.pointerEvents = 'auto';
            newButton.disabled = false;
            
            console.log('Location button fix applied successfully!');
        }
    }, 500);
    
    // Stop checking after 30 seconds
    setTimeout(() => clearInterval(checkInterval), 30000);
}