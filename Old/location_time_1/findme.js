const access_key = "3e3cd89b32d39af7119d79f8fe981803"

fetch('https://api.ipify.org?format=json')
  .then(response => response.json())
  .then(data => {
    fetch("api.ipstack.com/"+data.ip+"?access_key="+access_key)
	.then(response => response.json())
	.then(data => {
		console.log(data.latitude, data.longitude, data.city, data.region_name, data.country_name, data.continent_name)
	});
  })
  .catch(error => {
    console.error('Error fetching IP:', error);
  });