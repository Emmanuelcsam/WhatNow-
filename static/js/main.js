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
                }
            } else {
                console.error('Failed to get TTS audio:', data.message);
            }
        } catch (error) {
            console.error('Error playing introduction TTS:', error);
        }
    }

    // Step 1 -> Step 2 transition
    window.addEventListener('keypress', (event) => {
        if ((event.code === "Space" || event.code === "Enter") && step1 && !step1.classList.contains('d-none') && !step1.classList.contains('slide-left')) {
            goToStep2();
        }
    });

    nextBtn1.addEventListener('click', goToStep2);

    function goToStep2() {
        if (!step1 || !step2) return;
        
        step1.classList.add('slide-left');
        setTimeout(() => {
            step1.classList.add('d-none');
            step2.classList.remove('d-none');
            step2.classList.add('fade-in');
            if (nameInput) nameInput.focus();

            // Play step name instructions
            setTimeout(() => {
                playIntroductionTTS('step_name');
            }, 500);
        }, 800);
    }

    // Step 2 -> Step 3 transition
    function goToStep3() {
        if (!nameInput) return;
        
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
            twitter: twitterInput ? twitterInput.value.trim().replace('@', '') : '',
            instagram: instagramInput ? instagramInput.value.trim().replace('@', '') : '',
            github: githubInput ? githubInput.value.trim().replace('@', '') : '',
            linkedin: linkedinInput ? linkedinInput.value.trim().replace('@', '') : '',
            tiktok: tiktokInput ? tiktokInput.value.trim().replace('@', '') : '',
            youtube: youtubeInput ? youtubeInput.value.trim().replace('@', '') : ''
        };

        if (!step2 || !step3) return;
        
        step2.classList.add('slide-left');
        setTimeout(() => {
            step2.classList.add('d-none');
            step3.classList.remove('d-none');
            step3.classList.add('fade-in');
            if (activityInput) activityInput.focus();

            // Play step activity instructions
            setTimeout(() => {
                playIntroductionTTS('step_activity');
            }, 500);
        }, 800);
    }

    if (nextBtn2) nextBtn2.addEventListener('click', goToStep3);
    if (nameInput) {
        nameInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                goToStep3();
            }
        });
    }

    // Step 3 -> Step 4 transition
    function goToStep4() {
        if (!activityInput) return;
        
        const activity = activityInput.value.trim();
        if (!activity) {
            activityInput.focus();
            activityInput.classList.add('is-invalid');
            setTimeout(() => activityInput.classList.remove('is-invalid'), 3000);
            return;
        }

        if (!step3 || !step4) return;
        
        step3.classList.add('slide-left');
        setTimeout(() => {
            step3.classList.add('d-none');
            step4.classList.remove('d-none');
            step4.classList.add('fade-in');

            // Play step location instructions
            setTimeout(() => {
                playIntroductionTTS('step_location');
            }, 500);
        }, 800);
    }

    if (nextBtn3) nextBtn3.addEventListener('click', goToStep4);
    if (activityInput) {
        activityInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                goToStep4();
            }
        });
    }

    // Enhanced Location handling with multiple fallback methods
    async function getCurrentLocation() {
        console.log('getCurrentLocation called');
        
        // Show loading state
        if (locationSpinner) locationSpinner.classList.remove('d-none');
        if (locationMessage) {
            locationMessage.textContent = 'Getting your location...';
            locationMessage.classList.remove('d-none');
        }
        if (getLocationBtn) {
            getLocationBtn.disabled = true;
            getLocationBtn.classList.add('disabled');
        }

        try {
            // Try browser geolocation first for best accuracy
            if (navigator.geolocation) {
                if (locationMessage) locationMessage.textContent = 'Requesting browser location...';

                await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        async (position) => {
                            try {
                                const latitude = position.coords.latitude;
                                const longitude = position.coords.longitude;

                                if (locationMessage) locationMessage.textContent = 'Processing your location...';

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
                                    window.userLocation = userLocation; // Make it globally accessible
                                    
                                    if (locationSpinner) locationSpinner.classList.add('d-none');

                                    const confidence = Math.round(data.confidence * 100);
                                    const methods = data.methods_used.join(', ');

                                    if (locationMessage) {
                                        locationMessage.innerHTML = `
                                            <div class="text-success">
                                                <i class="fas fa-check-circle"></i>
                                                Location found: ${userLocation.city}, ${userLocation.state || userLocation.country}
                                                <br><small class="text-muted">Confidence: ${confidence}% (${methods})</small>
                                            </div>
                                        `;
                                    }

                                    // Auto-proceed to processing after a short delay
                                    setTimeout(() => {
                                        startProcessing();
                                    }, 1500);

                                    resolve();
                                } else {
                                    throw new Error('Could not determine location from coordinates');
                                }
                            } catch (error) {
                                console.error('Comprehensive location failed:', error);
                                reject(error);
                            }
                        },
                        (error) => {
                            console.error('Browser geolocation error:', error);
                            if (locationMessage) locationMessage.textContent = 'Browser location denied, trying IP-based detection...';
                            reject(error);
                        },
                        {
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 0
                        }
                    );
                });
            } else {
                throw new Error('Geolocation not supported');
            }
        } catch (error) {
            // Fall back to IP-based detection
            await fallbackToIPLocation();
        }
    }

    async function fallbackToIPLocation() {
        try {
            if (locationMessage) locationMessage.textContent = 'Using IP-based location detection...';

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
                window.userLocation = userLocation; // Make it globally accessible
                
                if (locationSpinner) locationSpinner.classList.add('d-none');

                const confidence = Math.round(data.confidence * 100);
                const methods = data.methods_used.join(', ');

                if (locationMessage) {
                    locationMessage.innerHTML = `
                        <div class="text-success">
                            <i class="fas fa-check-circle"></i>
                            Location found: ${userLocation.city}, ${userLocation.state || userLocation.country}
                            <br><small class="text-muted">Confidence: ${confidence}% (${methods})</small>
                        </div>
                    `;
                }

                // Auto-proceed to processing after a short delay
                setTimeout(() => {
                    startProcessing();
                }, 1500);
            } else {
                throw new Error('Could not determine location');
            }

        } catch (error) {
            console.error('Enhanced location detection failed:', error);
            if (locationSpinner) locationSpinner.classList.add('d-none');
            if (locationMessage) {
                locationMessage.innerHTML = `<div class="text-danger">Location detection failed. Please try again.</div>`;
            }
            if (getLocationBtn) {
                getLocationBtn.disabled = false;
                getLocationBtn.classList.remove('disabled');
                getLocationBtn.textContent = 'Try Again';
            }
        }
    }

    // Location button click handler
    if (getLocationBtn) {
        getLocationBtn.addEventListener('click', async function (e) {
            e.preventDefault();
            console.log('Share Location button clicked');
            await getCurrentLocation();
        });
    }

    // Make functions globally accessible for other scripts
    window.getCurrentLocation = getCurrentLocation;
    window.fallbackToIPLocation = fallbackToIPLocation;
    window.startProcessing = startProcessing;

    // Step 4 -> Processing flow
    async function startProcessing() {
        if (!userLocation) {
            if (locationMessage) {
                locationMessage.innerHTML = `<div class="text-warning">Please share your location first.</div>`;
            }
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
                    activity: activityInput ? activityInput.value.trim() : '',
                    social: userSocial
                })
            });

            const submitData = await submitResponse.json();

            if (submitData.success) {
                // Hide onboarding and show loading
                if (step4) step4.classList.add('slide-left');
                setTimeout(() => {
                    if (step4) step4.classList.add('d-none');
                    if (loadingSection) loadingSection.classList.remove('d-none');
                    if (loadingMessage) loadingMessage.textContent = submitData.message;

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
                    activity: activityInput ? activityInput.value.trim() : '',
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
                        activity: activityInput ? activityInput.value.trim() : '',
                        location: userLocation,
                        social: userSocial,
                        searchResults: data.search_summaries,
                        personalization_data: data.personalization_data
                    }));

                    // Redirect to map page
                    window.location.href = data.map_url;
                } else {
                    // Hide loading and show results
                    if (loadingSection) loadingSection.classList.add('d-none');
                    if (resultSection) resultSection.classList.remove('d-none');
                    if (resultContent) resultContent.textContent = data.result;
                }
            } else {
                // Show error in result section
                if (loadingSection) loadingSection.classList.add('d-none');
                if (resultSection) resultSection.classList.remove('d-none');
                if (resultContent) {
                    resultContent.textContent = 'Sorry, there was an error processing your request: ' + (data.message || 'Unknown error');
                }
            }
        } catch (error) {
            console.error('Error:', error);
            // Show error in result section
            if (loadingSection) loadingSection.classList.add('d-none');
            if (resultSection) resultSection.classList.remove('d-none');
            if (resultContent) {
                resultContent.textContent = 'Network error. Please check your connection and try again.';
            }
        }
    }

    // Handle restart button
    if (restartBtn) {
        restartBtn.addEventListener('click', function () {
            // Reset all inputs and variables
            if (nameInput) nameInput.value = '';
            if (activityInput) activityInput.value = '';
            if (twitterInput) twitterInput.value = '';
            if (instagramInput) instagramInput.value = '';
            if (githubInput) githubInput.value = '';
            if (linkedinInput) linkedinInput.value = '';
            if (tiktokInput) tiktokInput.value = '';
            if (youtubeInput) youtubeInput.value = '';
            
            userName = '';
            userSocial = {};
            userLocation = null;
            window.userLocation = null;

            // Reset location UI
            if (locationSpinner) locationSpinner.classList.add('d-none');
            if (locationMessage) {
                locationMessage.textContent = 'Click below to share your location';
                locationMessage.classList.add('d-none');
            }
            if (getLocationBtn) {
                getLocationBtn.disabled = false;
                getLocationBtn.textContent = 'Share Location';
            }

            // Clear result content
            if (resultContent) resultContent.textContent = '';

            // Reset to step 1
            if (loadingSection) loadingSection.classList.add('d-none');
            if (resultSection) resultSection.classList.add('d-none');
            if (step2) step2.classList.add('d-none');
            if (step3) step3.classList.add('d-none');
            if (step4) step4.classList.add('d-none');

            if (step1) {
                step1.classList.remove('d-none', 'slide-left');
            }
            if (step2) step2.classList.remove('fade-in', 'slide-left');
            if (step3) step3.classList.remove('fade-in', 'slide-left');
            if (step4) step4.classList.remove('fade-in', 'slide-left');

            // Focus on first step
            setTimeout(() => {
                if (nextBtn1) nextBtn1.focus();
            }, 100);
        });
    }
});

// Auto-initialize enhanced location detection when page loads
document.addEventListener('DOMContentLoaded', function () {
    // Initialize enhanced location detector if available
    if (typeof EnhancedLocationDetector !== 'undefined') {
        window.locationDetector = new EnhancedLocationDetector();

        // Set up callback for when location is detected
        window.locationDetector.onLocationDetected = function (location) {
            if (location && location.city) {
                window.userLocation = location;
                console.log('Enhanced location detected:', location);

                // Update UI if in location step
                const step4 = document.getElementById('step-4');
                const locationMessage = document.getElementById('location-message');
                const spinner = document.getElementById('location-spinner');
                const getLocationBtn = document.getElementById('get-location-btn');

                if (step4 && !step4.classList.contains('d-none') && locationMessage) {
                    if (spinner) spinner.classList.add('d-none');
                    locationMessage.innerHTML = `
                        <div class="text-success">
                            <i class="fas fa-check-circle"></i>
                            Location detected: ${location.city}, ${location.state || location.country}
                            <br><small class="text-muted">Auto-detected with ${Math.round((location.accuracy || 0.8) * 100)}% confidence</small>
                        </div>
                    `;

                    // Enable the continue button or auto-proceed
                    if (getLocationBtn) {
                        getLocationBtn.disabled = false;
                        getLocationBtn.textContent = 'Continue';
                        getLocationBtn.onclick = () => window.startProcessing();
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
});