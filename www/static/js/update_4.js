<!-- begin: update 4 statuses script -->
async function update4Statuses() {
    try {
        const response = await fetch(`{{ pfx }}{{ status_path }}`);
        const data = await response.json();
        if (response.ok) {
            const devices = Object.entries(data.devices);
            for (const [deviceId, device] of devices) {
                const button = document.getElementById(deviceId);
                const stateSpan = document.getElementById(`state-${deviceId}`);
                const powerSpan = document.getElementById(`power-${deviceId}`);

                button.style.setProperty('--status-color', device.state === 'on' ? '#d35400' : (device.state === 'off' ? '#448795' : 'gray'));
                stateSpan.textContent = device.state === 'on' ? 'ON' : (device.state === 'off' ? 'OFF' : '???');
                powerSpan.textContent = `Consumption: ${device.power || 0} W`;
            }
        }
    } catch (error) {
        console.error("Error during refreshing device states:", error);
    }
}

window.onload = update4Statuses;
// refresh
setInterval(update4Statuses, 6000);
<!-- end: update 4 statuses script -->