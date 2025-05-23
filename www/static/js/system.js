<!-- begin: system info script -->
    async function updateSystemInfo() {
        try {
            const response = await fetch(`{{ pfx }}{{ status_path }}`);
            const data = await response.json();
            if (response.ok) {
                const pwrSpan = document.getElementById(`pwr`);
                const osSpan = document.getElementById(`os`);
                const kernelSpan = document.getElementById(`kernel`);
                const coreSpan = document.getElementById(`cores`);
                const freqSpan = document.getElementById(`freq`);
                const cpuSpan = document.getElementById(`cpu`);
                const ramSpan = document.getElementById(`ram`);
                const tempSpan = document.getElementById(`temp`);

                pwrSpan.textContent = `Current total power consumption: ${data.devices.main.power || 0}W`;
                osSpan.textContent = `${data.system.os || "unknown"} ${data.system.osVersion || "unknown"}`;
                kernelSpan.textContent = `Kernel ${data.system.kernel || "unknown"}`;
                coreSpan.textContent = `Physical cores: ${data.system.cpuCores || 0}, logical cores: ${data.system.cpuThreads || 0}`;
                freqSpan.textContent = `Frequency: ${data.system.cpuFq || 0}Hz`;
                cpuSpan.textContent = `CPU load: ${data.system.cpu || 0}%`;
                ramSpan.textContent = `RAM usage: ${data.system.ram || 0}% of ${data.system.ramGB || 0}GB`;
                tempSpan.textContent = `Temperature: ${data.system.cpuTemp || 0}°C`;
                }
        } catch (error) {
            console.error("Error fetching system info:", error);
        }
    }

    window.onload = updateSystemInfo;
    // refresh
    setInterval(updateSystemInfo, 3000);
<!-- end: system info script -->