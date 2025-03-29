<!-- begin: toggle device script -->
async function toggleDevice(deviceId) {
        const button = document.getElementById(deviceId);
        const stateSpan = document.getElementById(`state-${deviceId}`);

        try {
            const response = await fetch(`{{ pfx }}/toggle/${deviceId}`, {method: 'POST'});
            const data = await response.json();
            if (response.ok) {
                const newState = data.state;
                button.style.setProperty('--status-color', newState === 'on' ? '#d35400' : (newState === 'off' ? '#448795' : 'gray'));
                stateSpan.textContent = newState === 'on' ? 'ON' : (newState === 'off' ? 'OFF' : '???');
            } else {
                alert(data.error || "Error during toggling socket.");
            }
        } catch (error) {
            console.error("Error during toggling device:", error);
            alert("Connection error, please try again.");
        }
    }
<!-- end: toggle device script -->