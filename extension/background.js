chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "api_analyze") {
        fetch('http://127.0.0.1:5000/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request.payload)
        })
        .then(res => res.json())
        .then(data => sendResponse({ success: true, data: data }))
        .catch(err => sendResponse({ success: false, error: err.toString() }));
        
        return true; // Keep channel open for async response
    }
    
    if (request.action === "open_details_page") {
        chrome.tabs.create({ url: chrome.runtime.getURL("details.html") });
    }
});
