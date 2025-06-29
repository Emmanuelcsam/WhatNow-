document.addEventListener('DOMContentLoaded', function () {
    // Onboarding elements
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');
    const step4 = document.getElementById('step-4');
    const nextBtn1 = document.getElementById('next-btn-1');
    const nextBtn2 = document.getElementById('next-btn-2');
    const nextBtn3 = document.getElementById('next-btn-3');
    const getLocationBtn = document.getElementById('get-location-btn');

    // Loading and result elements
    const loadingSection = document.getElementById('loading-section');
    const resultSection = document.getElementById('result-section');
    const loadingMessage = document.getElementById('loading-message');
    const resultContent = document.getElementById('result-content');
    const restartBtn = document.getElementById('restart-btn');

    // Location elements
    const locationSpinner = document.getElementById('location-spinner');
    const locationMessage = document.getElementById('location-message');

    // Form inputs
    const nameInput = document.getElementById('user-name');
    const activityInput = document.getElementById('user-activity');
    const twitterInput = document.getElementById('user-twitter');
    const instagramInput = document.getElementById('user-instagram');
    const githubInput = document.getElementById('user-github');
    const linkedinInput = document.getElementById('user-linkedin');
    const tiktokInput = document.getElementById('user-tiktok');
    const youtubeInput = document.getElementById('user-youtube');

    let userName = '';
    let userSocial = {};
    let userLocation = null;

    // TTS functionality
    async function playIntroductionTTS(step, locationData = null) {
        try {
            const requestBody = locationData ? { location: locationData } : {};

            const response = await fetch(`/tts/introduction/${step}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (data.success && data.audio_id) {
                const audio = new Audio(`/audio/${data.audio_id}`);

                // Auto-play with user interaction fallback
                try {
                    await audio.play();
                    console.log(`Playing TTS for step: ${step}`);
                } catch (e) {
                    console.log('Auto-play blocked, user interaction required');
                    // Could show a play button here if needed
                }
            } else {
                console.error('Failed to get TTS audio:', data.message);
            }
        } catch (error) {
            console.error('Error playing introduction TTS:', error);
        }
    }

    // Function to play welcome message (after user interaction)
    function playWelcomeIfNeeded() {
        // Welcome audio removed - this function is now empty but kept for compatibility
    }

    // Step 1 -> Step 2 transition
    window.addEventListener('keypress', (event) => {
        if ((event.code == "Space" || event.code == "Enter") && !step1.classList.contains('slide-left')) {
            step1.classList.add('slide-left');
            setTimeout(() => {
                step1.classList.add('d-none');
                step2.classList.remove('d-none');
                step2.classList.add('fade-in');
                nameInput.focus();

                // Play step name instructions
                setTimeout(() => {
                    playIntroductionTTS('step_name');
                }, 500);
            }, 800);
        }
    });

    nextBtn1.addEventListener('click', function () {
        step1.classList.add('slide-left');
        setTimeout(() => {
            step1.classList.add('d-none');
            step2.classList.remove('d-none');
            step2.classList.add('fade-in');
            nameInput.focus();

            // Play step name instructions
            setTimeout(() => {
                playIntroductionTTS('step_name');
            }, 500);
        }, 800);
    });

    // Step 2 -> Step 3 transition
    function goToStep3() {
        const name = nameInput.value.trim();
        if (!name) {
            nameInput.focus();
            nameInput.classList.add('is-invalid');
            setTimeout(() => nameInput.classList.remove('is-invalid'), 3000);
            return;
        }

        userName = name;

        // Capture social media handles (optional)
        userSocial = {
            twitter: twitterInput.value.trim().replace('@', ''), // Remove @ if user added it
            instagram: instagramInput.value.trim().replace('@', ''), // Remove @ if user added it
            github: githubInput.value.trim().replace('@', ''), // Remove @ if user added it
            linkedin: linkedinInput.value.trim().replace('@', ''), // Remove @ if user added it
            tiktok: tiktokInput.value.trim().replace('@', ''), // Remove @ if user added it
            youtube: youtubeInput.value.trim().replace('@', '') // Remove @ if user added it
        };

        step2.classList.add('slide-left');
        setTimeout(() => {
            step2.classList.add('d-none');
            step3.classList.remove('d-none');
            step3.classList.add('fade-in');
            activityInput.focus();

            // Play step activity instructions
            setTimeout(() => {
                playIntroductionTTS('step_activity');
            }, 500);
        }, 800);
    }

    nextBtn2.addEventListener('click', goToStep3);
    nameInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            goToStep3();
        }
    });

    // Step 3 -> Step 4 transition
    function goToStep4() {
        const activity = activityInput.value.trim();
        if (!activity) {
            activityInput.focus();
            activityInput.classList.add('is-invalid');
            setTimeout(() => activityInput.classList.remove('is-invalid'), 3000);
            return;
        }

        step3.classList.add('slide-left');
        setTimeout(() => {
            step3.classList.add('d-none');
            step4.classList.remove('d-none');
            step4.classList.add('fade-in');
            
            // Setup location button when step 4 is visible
            setupLocationButton();

            // Play step location instructions
            setTimeout(() => {
                playIntroductionTTS('step_location');
            }, 500);
        }, 800);
    }

    nextBtn3.addEventListener('click', goToStep4);
    activityInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            goToStep4();
        }
    });

    // Enhanced Location handling with multiple fallback methods
    async function getCurrentLocation() {
        console.log('getCurrentLocation called');
        return new Promise(async (resolve, reject) => {
            // Get fresh references to UI elements
            const spinner = document.getElementById('location-spinner');
            const message = document.getElementById('location-message');
            const btn = document.getElementById('get-location-btn');
            
            // Ensure we have the UI elements
            if (!spinner || !message || !btn) {
                console.error('Missing UI elements:', {
                    spinner: !!spinner,
                    message: !!message,
                    btn: !!btn
                });
                reject(new Error('UI elements not found'));
                return;
            }
            
            console.log('Starting location detection UI update');
            spinner.classList.remove('d-none');
            message.textContent = 'Getting your location...';
            btn.disabled = true;
            btn.classList.add('disabled');

            try {
                // Try browser geolocation first for best accuracy
                if (navigator.geolocation) {
                    message.textContent = 'Requesting browser location...';
                    
                    navigator.geolocation.getCurrentPosition(
                        async (position) => {
                            try {
                                const latitude = position.coords.latitude;
                                const longitude = position.coords.longitude;
                                
                                message.textContent = 'Processing your location...';
                                
                                // Use comprehensive location detection with browser coordinates
                                const response = await fetch('/api/location/comprehensive', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({
                                        latitude: latitude,
                                        longitude: longitude
                                    })
                                });

                                const data = await response.json();

                                if (data.primary_location) {
                                    userLocation = data.primary_location;
                                    spinner.classList.add('d-none');

                                    const confidence = Math.round(data.confidence * 100);
                                    const methods = data.methods_used.join(', ');

                                    message.innerHTML = `
                                        <div class="text-success">
                                            <i class="bi bi-check-circle"></i>
                                            Location found: ${userLocation.city}, ${userLocation.state || userLocation.country}
                                            <br><small class="text-muted">Confidence: ${confidence}% (${methods})</small>
                                        </div>
                                    `;

                                    // Auto-proceed to processing after a short delay
                                    setTimeout(() => {
                                        startProcessing();
                                    }, 1500);

                                    resolve(userLocation);
                                } else {
                                    throw new Error('Could not determine location from coordinates');
                                }
                            } catch (error) {
                                console.error('Comprehensive location failed:', error);
                                // Fall back to IP-based detection
                                fallbackToIPLocation(resolve, reject);
                            }
                        },
                        (error) => {
                            console.error('Browser geolocation error:', error);
                            message.textContent = 'Browser location denied, trying IP-based detection...';
                            // Fall back to IP-based detection
                            fallbackToIPLocation(resolve, reject);
                        },
                        {
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 0
                        }
                    );
                } else {
                    // No browser geolocation, try IP-based detection
                    fallbackToIPLocation(resolve, reject);
                }
            } catch (error) {
                console.error('Location detection error:', error);
                spinner.classList.add('d-none');
                message.innerHTML = `<div class="text-danger">Location detection failed. Please try again.</div>`;
                btn.disabled = false;
                btn.textContent = 'Try Again';
                reject(error);
            }
        });
    }
    
    async function fallbackToIPLocation(resolve, reject) {
        try {
            const message = document.getElementById('location-message');
            const spinner = document.getElementById('location-spinner');
            const btn = document.getElementById('get-location-btn');
            
            if (message) message.textContent = 'Using IP-based location detection...';
            
            const response = await fetch('/api/location/comprehensive', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            });

            const data = await response.json();

            if (data.primary_location) {
                userLocation = data.primary_location;
                spinner.classList.add('d-none');

                const confidence = Math.round(data.confidence * 100);
                const methods = data.methods_used.join(', ');

                message.innerHTML = `
                    <div class="text-success">
                        <i class="bi bi-check-circle"></i>
                        Location found: ${userLocation.city}, ${userLocation.state || userLocation.country}
                        <br><small class="text-muted">Confidence: ${confidence}% (${methods})</small>
                    </div>
                `;

                // Auto-proceed to processing after a short delay
                setTimeout(() => {
                    startProcessing();
                }, 1500);

                resolve(userLocation);
            } else {
                throw new Error('Could not determine location');
            }

        } catch (error) {
            console.error('Enhanced location detection failed:', error);
            spinner.classList.add('d-none');
            message.innerHTML = `<div class="text-danger">Location detection failed. Please try again.</div>`;
            btn.disabled = false;
            btn.classList.remove('disabled');
            btn.textContent = 'Try Again';
            reject(error);
        }
    }

    function useDefaultLocation() {
        userLocation = {
            country: 'Global',
            city: 'Unknown',
            zipcode: 'Unknown',
            latitude: null,
            longitude: null,
            full_address: 'Default location'
        };

        spinner.classList.add('d-none');
        message.innerHTML = `
            <div class="text-info">
                Using default location settings
            </div>
        `;

        setTimeout(() => {
            startProcessing();
        }, 1000);
    }

    // Setup location button when step 4 becomes visible
    function setupLocationButton() {
        // Get fresh reference to button
        const locationBtn = document.getElementById('get-location-btn');
        if (!locationBtn) {
            console.error('Location button not found!');
            return;
        }
        
        // Remove any existing event listeners by cloning the button
        const newBtn = locationBtn.cloneNode(true);
        locationBtn.parentNode.replaceChild(newBtn, locationBtn);
        
        console.log('Setting up location button event listener');
        
        // Add click event listener
        newBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Share Location button clicked - event triggered');
            
            // Disable button immediately for visual feedback
            this.disabled = true;
            this.style.pointerEvents = 'none';
            
            try {
                await getCurrentLocation();
            } catch (error) {
                console.error('Location detection failed:', error);
                // Re-enable button on error
                this.disabled = false;
                this.style.pointerEvents = 'auto';
                this.textContent = 'Try Again';
            }
        });
        
        // Make sure button is enabled and clickable
        newBtn.disabled = false;
        newBtn.style.pointerEvents = 'auto';
        newBtn.style.cursor = 'pointer';
        
        console.log('Location button setup complete');
    }

    // Step 4 -> Processing flow
    async function startProcessing() {
        if (!userLocation) {
            useDefaultLocation();
            return;
        }

        try {
            // First, show initial response and loading screen
            const submitResponse = await fetch('/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: userName,
                    activity: activityInput.value.trim(),
                    social: userSocial
                })
            });

            const submitData = await submitResponse.json();

            if (submitData.success) {
                // Hide onboarding and show loading
                step4.classList.add('slide-left');
                setTimeout(() => {
                    step4.classList.add('d-none');
                    loadingSection.classList.remove('d-none');
                    loadingMessage.textContent = submitData.message;

                    // Play processing instructions with location context
                    setTimeout(() => {
                        playIntroductionTTS('processing', userLocation);
                    }, 500);
                }, 800);

                // Start background processing
                processInBackground();
            } else {
                alert(submitData.message || 'Something went wrong. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Network error. Please check your connection and try again.');
        }
    }

    async function processInBackground() {
        try {
            const response = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: userName,
                    activity: activityInput.value.trim(),
                    location: userLocation,
                    social: userSocial
                })
            });

            const data = await response.json();

            if (data.success) {
                // Check if we should redirect to map
                if (data.redirect_to_map && data.map_url) {
                    // Store user data for the map page with enhanced personalization data
                    sessionStorage.setItem('userData', JSON.stringify({
                        name: userName,
                        activity: activityInput.value.trim(),
                        location: userLocation,
                        social: userSocial,
                        searchResults: data.search_summaries,
                        personalization_data: data.personalization_data  // Include personalization data
                    }));

                    // Redirect to map page
                    window.location.href = data.map_url;
                } else {
                    // Hide loading and show results
                    loadingSection.classList.add('d-none');
                    resultSection.classList.remove('d-none');
                    resultContent.textContent = data.result;
                }
            } else {
                // Show error in result section
                loadingSection.classList.add('d-none');
                resultSection.classList.remove('d-none');
                resultContent.textContent = 'Sorry, there was an error processing your request: ' + (data.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Error:', error);
            // Show error in result section
            loadingSection.classList.add('d-none');
            resultSection.classList.remove('d-none');
            resultContent.textContent = 'Network error. Please check your connection and try again.';
        }
    }

    // Handle restart button
    restartBtn.addEventListener('click', function () {
        // Reset all inputs and variables
        nameInput.value = '';
        activityInput.value = '';
        twitterInput.value = '';
        instagramInput.value = '';
        userName = '';
        userSocial = {};
        userLocation = null;

        // Reset location UI
        spinner.classList.add('d-none');
        locationMessage.textContent = 'Click below to share your location';
        btn.disabled = false;
        getLocationBtn.textContent = 'Share Location';

        // Clear result content
        resultContent.textContent = '';

        // Reset to step 1
        loadingSection.classList.add('d-none');
        resultSection.classList.add('d-none');
        step2.classList.add('d-none');
        step3.classList.add('d-none');
        step4.classList.add('d-none');

        step1.classList.remove('d-none', 'slide-left');
        step2.classList.remove('fade-in', 'slide-left');
        step3.classList.remove('fade-in', 'slide-left');
        step4.classList.remove('fade-in', 'slide-left');

        // Focus on first step
        setTimeout(() => {
            nextBtn1.focus();
        }, 100);
    });
});

// Enhanced Location Detection Integration
// Auto-initialize enhanced location detection when page loads
document.addEventListener('DOMContentLoaded', function () {
    // Initialize enhanced location detector if available
    if (typeof EnhancedLocationDetector !== 'undefined') {
        window.locationDetector = new EnhancedLocationDetector();

        // Set up callback for when location is detected
        window.locationDetector.onLocationDetected = function (location) {
            if (location && location.city) {
                userLocation = location;
                console.log('Enhanced location detected:', location);

                // Update UI if in location step
                if (step4 && !step4.classList.contains('d-none') && locationMessage) {
                    spinner.classList.add('d-none');
                    message.innerHTML = `
                        <div class="text-success">
                            <i class="bi bi-check-circle"></i>
                            Location detected: ${location.city}, ${location.state || location.country}
                            <br><small class="text-muted">Auto-detected with ${Math.round((location.accuracy || 0.8) * 100)}% confidence</small>
                        </div>
                    `;

                    // Enable the continue button or auto-proceed
                    if (getLocationBtn) {
                        btn.disabled = false;
                        getLocationBtn.textContent = 'Continue';
                        getLocationBtn.onclick = () => startProcessing();
                    }
                }
            }
        };

        // Auto-detect location if user hasn't declined
        if (!localStorage.getItem('userDeclinedLocation')) {
            setTimeout(() => {
                window.locationDetector.detectLocation();
            }, 2000); // Wait 2 seconds after page load
        }
    }

    // Rest of existing DOMContentLoaded code...
});
