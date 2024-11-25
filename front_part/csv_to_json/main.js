document.getElementById('start-scraping').addEventListener('click', async () => {
    const fileInput = document.getElementById('csv-file');
    const statusElement = document.getElementById('status');

    if (!fileInput.files.length) {
        alert('Please upload a CSV file!');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Inform user that the upload is in progress
        statusElement.textContent = 'Uploading file... Please wait.';

        // Upload CSV to the backend
        const uploadResponse = await fetch('http://127.0.0.1:5000/upload', {
            method: 'POST',
            body: formData,
        });
        if (!uploadResponse.ok) throw new Error('Error uploading CSV file');

        // Inform user that scraping has started
        statusElement.textContent = 'File uploaded successfully. Starting scraping process... Please wait.';

        // Start scraping
        const scrapeResponse = await fetch('http://127.0.0.1:5000/scrape');
        const scrapeResult = await scrapeResponse.json();

        if (scrapeResponse.ok) {
            // Provide the download link for the user
            statusElement.textContent = 'Scraping completed successfully. Click the link below to download:';

            // Create a clickable download link
            const downloadLink = document.createElement('a');
            downloadLink.href = 'http://127.0.0.1:5000/grouped_scraped_data.json';
            downloadLink.textContent = 'Download grouped_scraped_data.json';
            downloadLink.download = 'grouped_scraped_data.json'; // Ensure it downloads instead of opening

            // Append link to the status element
            statusElement.appendChild(downloadLink);
        } else {
            throw new Error(scrapeResult.error);
        }
    } catch (error) {
        statusElement.textContent = `Error: ${error.message}`;
    }
});
