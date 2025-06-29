/**
 * Enhanced Location Detection Client
 *
 * Provides comprehensive location detection using multiple methods:
 * - Browser Geolocation API (most accurate)
 * - IP-based location detection (fallback)
 * - User input validation and correction
 */

class EnhancedLocationDetector {
    constructor() {
        this.currentLocation = null;
        this.locationHistory = [];
        this.isDetecting = false;

        // Configuration
        this.config = {
            timeout: 10000, // 10 seconds
            enableHighAccuracy: true,
            maximumAge: 300000, // 5 minutes
            fallbackToIP: true,
            validateResults: true
        };

        this.init();
    }

    init() {
        console.log('Enhanced Location Detector initialized');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for location detection requests
        document.addEventListener('requestLocation', (event) => {
            this.detectLocation(event.detail?.callback);
        });

        // Auto-detect on page load if enabled
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                if (this.shouldAutoDetect()) {
                    this.detectLocation();
                }
            });
        } else if (this.shouldAutoDetect()) {
            this.detectLocation();
        }
    }

    shouldAutoDetect() {
        // Check if we should automatically detect location
        return !localStorage.getItem('userDeclinedLocation') &&
            !this.currentLocation;
    }

    async detectLocation(callback = null) {
        if (this.isDetecting) {
            console.log('Location detection already in progress');
            return;
        }

        this.isDetecting = true;
        this.showLocationStatus('Detecting your location...', 'detecting');

        try {
            let locationResult = null;

            // Try browser geolocation first (most accurate)
            if (navigator.geolocation) {
                try {
                    locationResult = await this.getBrowserLocation();
                    console.log('Got browser location:', locationResult);
                } catch (error) {
                    console.warn('Browser geolocation failed:', error);
                }
            }

            // Fallback to IP-based location
            if (!locationResult && this.config.fallbackToIP) {
                try {
                    locationResult = await this.getIPLocation();
                    console.log('Got IP location:', locationResult);
                } catch (error) {
                    console.warn('IP location failed:', error);
                }
            }

            if (locationResult) {
                // Validate and enhance the location data
                const enhancedLocation = await this.enhanceLocationData(locationResult);

                this.currentLocation = enhancedLocation;
                this.locationHistory.push({
                    ...enhancedLocation,
                    timestamp: new Date().toISOString()
                });

                this.showLocationStatus(
                    `Location detected: ${enhancedLocation.city}, ${enhancedLocation.state}`,
                    'success'
                );

                // Store in session for this visit
                sessionStorage.setItem('detectedLocation', JSON.stringify(enhancedLocation));

                // Notify application
                this.notifyLocationDetected(enhancedLocation);

                if (callback) {
                    callback(enhancedLocation);
                }

                return enhancedLocation;

            } else {
                throw new Error('All location detection methods failed');
            }

        } catch (error) {
            console.error('Location detection failed:', error);
            this.showLocationStatus('Location detection failed. Please enter manually.', 'error');
            this.showLocationInput();

            if (callback) {
                callback(null, error);
            }

            return null;

        } finally {
            this.isDetecting = false;
        }
    }

    getBrowserLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }

            const options = {
                enableHighAccuracy: this.config.enableHighAccuracy,
                timeout: this.config.timeout,
                maximumAge: this.config.maximumAge
            };

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const location = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        source: 'browser_geolocation',
                        timestamp: new Date().toISOString()
                    };
                    resolve(location);
                },
                (error) => {
                    let errorMessage = 'Unknown geolocation error';
                    switch (error.code) {
                        case error.PERMISSION_DENIED:
                            errorMessage = 'Location access denied by user';
                            localStorage.setItem('userDeclinedLocation', 'true');
                            break;
                        case error.POSITION_UNAVAILABLE:
                            errorMessage = 'Location information unavailable';
                            break;
                        case error.TIMEOUT:
                            errorMessage = 'Location request timed out';
                            break;
                    }
                    reject(new Error(errorMessage));
                },
                options
            );
        });
    }

    async getIPLocation() {
        try {
            // Use the exact approach from the user's example, but enhanced
            console.log('Detecting IP and location using IPStack method...');

            // Step 1: Get user's IP using ipify (as in the example)
            const ipResponse = await fetch('https://api.ipify.org?format=json');
            if (!ipResponse.ok) {
                throw new Error('Failed to get IP address from ipify');
            }

            const ipData = await ipResponse.json();
            const userIP = ipData.ip;
            console.log('Detected IP:', userIP);

            // Step 2: Use our enhanced backend API (which uses IPStack and fallbacks)
            const locationResponse = await fetch('/api/location/from-ip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ip: userIP })
            });

            if (!locationResponse.ok) {
                throw new Error(`Backend location API failed: ${locationResponse.status}`);
            }

            const locationData = await locationResponse.json();

            if (locationData.error) {
                throw new Error(locationData.error);
            }

            // Log the exact data that user's example would get
            console.log('Enhanced location data:', {
                latitude: locationData.latitude,
                longitude: locationData.longitude,
                city: locationData.city,
                region_name: locationData.state,
                country_name: locationData.country,
                continent_name: locationData.continent,
                zip_code: locationData.zip_code,
                accuracy: locationData.accuracy,
                source: locationData.source
            });

            return {
                ...locationData,
                source: 'enhanced_ip_detection',
                timestamp: new Date().toISOString(),
                detected_ip: userIP
            };

        } catch (error) {
            console.error('Enhanced IP location detection failed:', error);

            // Fallback: Try direct IPStack call (as backup)
            try {
                return await this.getIPLocationDirect();
            } catch (fallbackError) {
                console.error('Direct IPStack fallback also failed:', fallbackError);
                throw error;
            }
        }
    }

    async getIPLocationDirect() {
        try {
            // Direct implementation of user's example (as fallback)
            const access_key = "3e3cd89b32d39af7119d79f8fe981803"; // From secrets.txt

            const ipResponse = await fetch('https://api.ipify.org?format=json');
            const ipData = await ipResponse.json();

            const locationResponse = await fetch(`https://api.ipstack.com/${ipData.ip}?access_key=${access_key}&fields=country_name,country_code,region_name,region_code,city,zip,latitude,longitude,time_zone,continent_name`);
            const locationData = await locationResponse.json();

            if (locationData.success === false) {
                throw new Error(locationData.error?.info || 'IPStack API error');
            }

            console.log('Direct IPStack result:', {
                latitude: locationData.latitude,
                longitude: locationData.longitude,
                city: locationData.city,
                region_name: locationData.region_name,
                country_name: locationData.country_name,
                continent_name: locationData.continent_name
            });

            return {
                latitude: locationData.latitude,
                longitude: locationData.longitude,
                city: locationData.city || '',
                state: locationData.region_name || '',
                country: locationData.country_name || '',
                country_code: locationData.country_code || '',
                zip_code: locationData.zip || '',
                timezone: locationData.time_zone?.id || locationData.time_zone || '',
                continent: locationData.continent_name || '',
                region_code: locationData.region_code || '',
                accuracy: 0.85, // IPStack is generally accurate
                source: 'direct_ipstack',
                timestamp: new Date().toISOString(),
                detected_ip: ipData.ip
            };

        } catch (error) {
            console.error('Direct IPStack call failed:', error);
            throw error;
        }
    }

    async enhanceLocationData(locationData) {
        try {
            // If we have coordinates but missing address data, reverse geocode
            if (locationData.latitude && locationData.longitude &&
                (!locationData.city || !locationData.state)) {

                const response = await fetch('/api/location/reverse-geocode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        latitude: locationData.latitude,
                        longitude: locationData.longitude
                    })
                });

                if (response.ok) {
                    const geocodeData = await response.json();
                    return {
                        ...locationData,
                        ...geocodeData,
                        enhanced: true
                    };
                }
            }

            return locationData;

        } catch (error) {
            console.warn('Location enhancement failed:', error);
            return locationData;
        }
    }

    notifyLocationDetected(location) {
        // Dispatch custom event
        const event = new CustomEvent('locationDetected', {
            detail: { location }
        });
        document.dispatchEvent(event);

        // Update any location display elements
        this.updateLocationDisplay(location);

        // Update forms with location data
        this.updateLocationForms(location);
    }

    updateLocationDisplay(location) {
        const displays = document.querySelectorAll('[data-location-display]');
        displays.forEach(display => {
            const format = display.dataset.locationDisplay;
            let text = '';

            switch (format) {
                case 'city-state':
                    text = `${location.city}, ${location.state}`;
                    break;
                case 'full':
                    text = `${location.city}, ${location.state}, ${location.country}`;
                    break;
                case 'city':
                    text = location.city;
                    break;
                default:
                    text = `${location.city}, ${location.state}`;
            }

            display.textContent = text;
        });
    }

    updateLocationForms(location) {
        // Update location input fields
        const cityInputs = document.querySelectorAll('input[name="city"], input[name="location"]');
        cityInputs.forEach(input => {
            if (!input.value) {
                input.value = location.city;
                input.dispatchEvent(new Event('change'));
            }
        });

        const stateInputs = document.querySelectorAll('input[name="state"]');
        stateInputs.forEach(input => {
            if (!input.value) {
                input.value = location.state;
                input.dispatchEvent(new Event('change'));
            }
        });

        // Update hidden coordinate fields
        const latInputs = document.querySelectorAll('input[name="latitude"]');
        latInputs.forEach(input => {
            input.value = location.latitude || '';
        });

        const lonInputs = document.querySelectorAll('input[name="longitude"]');
        lonInputs.forEach(input => {
            input.value = location.longitude || '';
        });
    }

    showLocationStatus(message, type = 'info') {
        // Find or create status display
        let statusElement = document.getElementById('location-status');
        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.id = 'location-status';
            statusElement.className = 'location-status';

            // Try to insert near location-related elements
            const locationForm = document.querySelector('form[data-location-form]') ||
                document.querySelector('#search-form') ||
                document.body;

            if (locationForm.tagName === 'FORM') {
                locationForm.insertBefore(statusElement, locationForm.firstChild);
            } else {
                locationForm.appendChild(statusElement);
            }
        }

        statusElement.textContent = message;
        statusElement.className = `location-status ${type}`;

        // Auto-hide success and error messages
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                if (statusElement.parentNode) {
                    statusElement.style.opacity = '0';
                    setTimeout(() => {
                        if (statusElement.parentNode && statusElement.style.opacity === '0') {
                            statusElement.remove();
                        }
                    }, 300);
                }
            }, 5000);
        }
    }

    showLocationInput() {
        // Show manual location input if auto-detection fails
        const locationInputs = document.querySelectorAll('input[name="city"], input[name="location"]');
        locationInputs.forEach(input => {
            input.style.display = 'block';
            input.focus();
        });

        // Show location correction UI if available
        const locationCorrection = document.getElementById('location-correction');
        if (locationCorrection) {
            locationCorrection.style.display = 'block';
        }
    }

    // Public methods for manual interaction
    requestPermission() {
        return this.detectLocation();
    }

    getCurrentLocation() {
        return this.currentLocation;
    }

    setLocation(location) {
        this.currentLocation = location;
        this.notifyLocationDetected(location);
        sessionStorage.setItem('detectedLocation', JSON.stringify(location));
    }

    clearLocation() {
        this.currentLocation = null;
        sessionStorage.removeItem('detectedLocation');
        localStorage.removeItem('userDeclinedLocation');
    }
}

// Initialize the enhanced location detector
const locationDetector = new EnhancedLocationDetector();

// Export for global access
window.LocationDetector = locationDetector;

// Utility functions for easy integration
window.detectLocation = (callback) => locationDetector.detectLocation(callback);
window.getCurrentLocation = () => locationDetector.getCurrentLocation();
window.setLocation = (location) => locationDetector.setLocation(location);
