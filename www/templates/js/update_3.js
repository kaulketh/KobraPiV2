<!-- begin: update 3 statuses script -->
async function update3Statuses() {
    try {
        const response = await fetch(`{{ pfx }}{{ status_path }}`);
        const data = await response.json();
        if (response.ok) {
            const totPwrSpan = document.getElementById(`pwr`);
            totPwrSpan.textContent = `Current total power consumption: ${data.devices.main.power || 0}W`;

            const devices = [...Object.entries(data.devices).slice(0, 2), ...Object.entries(data.devices).slice(3)];
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

window.onload = update3Statuses;
// refresh
setInterval(update3Statuses, 5000);
<!-- end: update 3 statuses script -->