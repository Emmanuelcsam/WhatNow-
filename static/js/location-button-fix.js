// Location Button Fix - Ensures the location button works correctly
console.log('Location button fix loading...');

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLocationButtonFix);
} else {
    initLocationButtonFix();
}

function initLocationButtonFix() {
    console.log('Initializing location button fix...');
    
    // Use MutationObserver to detect when step 4 becomes visible
    const observer = new MutationObserver((mutations) => {
        const step4 = document.getElementById('step-4');
        const button = document.getElementById('get-location-btn');
        
        if (step4 && button && !step4.classList.contains('d-none')) {
            console.log('Step 4 is now visible, ensuring button works...');
            ensureLocationButtonWorks();
        }
    });
    
    // Start observing
    const step4 = document.getElementById('step-4');
    if (step4) {
        observer.observe(step4, { 
            attributes: true, 
            attributeFilter: ['class'] 
        });
    }
    
    // Also check periodically as a fallback
    const checkInterval = setInterval(() => {
        const button = document.getElementById('get-location-btn');
        const step4 = document.getElementById('step-4');
        
        if (button && step4 && !step4.classList.contains('d-none')) {
            console.log('Location button and step 4 found!');
            clearInterval(checkInterval);
            ensureLocationButtonWorks();
        }
    }, 100);
    
    // Stop checking after 30 seconds
    setTimeout(() => clearInterval(checkInterval), 30000);
}

function ensureLocationButtonWorks() {
    const button = document.getElementById('get-location-btn');
    if (!button) {
        console.error('Location button not found!');
        return;
    }
    
    // Remove any existing event listeners by cloning
    const newButton = button.cloneNode(true);
    button.parentNode.replaceChild(newButton, button);
    
    console.log('Setting up fresh click handler for location button');
    
    // Add click event listener
    newButton.addEventListener('click', async function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('Location button clicked!');
        
        // Disable button for visual feedback
        this.disabled = true;
        this.textContent = 'Detecting location...';
        this.style.cursor = 'wait';
        
        try {
            // Check if getCurrentLocation is available
            if (typeof window.getCurrentLocation === 'function') {
                console.log('Using window.getCurrentLocation()');
                await window.getCurrentLocation();
            } else {
                console.error('getCurrentLocation not found, using direct API call');
                
                // Direct API call as fallback
                const spinner = document.getElementById('location-spinner');
                const message = document.getElementById('location-message');
                
                if (spinner) spinner.classList.remove('d-none');
                if (message) message.textContent = 'Getting your location...';
                
                const response = await fetch('/api/location/comprehensive', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({})
                });
                
                const data = await response.json();
                console.log('Location data received:', data);
                
                if (data.primary_location) {
                    // Store location globally
                    window.userLocation = data.primary_location;
                    
                    // Update UI
                    if (spinner) spinner.classList.add('d-none');
                    if (message) {
                        const confidence = Math.round(data.confidence * 100);
                        const methods = data.methods_used ? data.methods_used.join(', ') : 'IP-based';
                        
                        message.innerHTML = `
                            <div class="text-success">
                                <i class="fas fa-check-circle"></i>
                                Location found: ${data.primary_location.city}, ${data.primary_location.state || data.primary_location.country}
                                <br><small class="text-muted">Confidence: ${confidence}% (${methods})</small>
                            </div>
                        `;
                    }
                    
                    // Auto-proceed after a short delay
                    setTimeout(() => {
                        if (typeof window.startProcessing === 'function') {
                            console.log('Auto-starting processing...');
                            window.startProcessing();
                        } else {
                            console.log('startProcessing not found, user needs to continue manually');
                            this.textContent = 'Continue';
                            this.disabled = false;
                            this.style.cursor = 'pointer';
                        }
                    }, 1500);
                } else {
                    throw new Error('No location data received');
                }
            }
        } catch (error) {
            console.error('Location detection error:', error);
            
            const message = document.getElementById('location-message');
            if (message) {
                message.innerHTML = '<div class="text-danger">Location detection failed. Please try again.</div>';
            }
            
            // Re-enable button
            this.disabled = false;
            this.textContent = 'Try Again';
            this.style.cursor = 'pointer';
        }
    });
    
    // Ensure button is properly styled and enabled
    newButton.disabled = false;
    newButton.style.cursor = 'pointer';
    newButton.style.pointerEvents = 'auto';
    newButton.classList.remove('disabled');
    
    console.log('Location button setup complete!');
}