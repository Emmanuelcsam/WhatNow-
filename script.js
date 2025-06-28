function searchEvents() {
    const keyword = document.getElementById("keyword").value.trim();
    if (!keyword) {
        alert("Please enter a keyword.");
        return;
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const { latitude, longitude } = position.coords;

            fetch("/find_events", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    lat: latitude,
                    lon: longitude,
                    keyword: keyword
                })
            })
            .then(res => res.json())
            .then(events => {
                const list = document.getElementById("results");
                list.innerHTML = "";
                if (events.length === 0) {
                    list.innerHTML = "<li>No events found for that keyword in your area.</li>";
                } else {
                    events.forEach(e => {
                        const item = document.createElement("li");
                        item.innerHTML = `<strong>${e.name}</strong><br>${e.location}<br><em>${e.start_time}</em><br><a href="${e.url}" target="_blank">More Info</a>`;
                        list.appendChild(item);
                    });
                }
            });
        });
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}
