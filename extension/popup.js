document.getElementById('reportBtn').addEventListener('click', async () => {
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('errorMsg').classList.add('hidden');
    document.getElementById('successMsg').classList.add('hidden');
    
    let btn = document.getElementById('reportBtn');
    btn.disabled = true;

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        chrome.tabs.sendMessage(tab.id, { action: "extract_job_info" }, function(response) {
            if (chrome.runtime.lastError || !response) {
                showError("Could not extract info. Please refresh the page.");
                btn.disabled = false;
                return;
            }

            // Call Backend API to report
            fetch('http://127.0.0.1:5000/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: response.company,
                    job_title: response.title,
                    description: response.description
                })
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('loading').classList.add('hidden');
                document.getElementById('successMsg').innerText = "Reported successfully!";
                document.getElementById('successMsg').classList.remove('hidden');
            })
            .catch(err => {
                showError("Cannot connect to server.");
                btn.disabled = false;
            });
        });
    } catch (error) {
         showError("Check if you are on a compatible page.");
         btn.disabled = false;
    }
});

function showError(msg) {
    document.getElementById('loading').classList.add('hidden');
    let errorMsg = document.getElementById('errorMsg');
    errorMsg.innerText = msg;
    errorMsg.classList.remove('hidden');
}
