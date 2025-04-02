require("dotenv").config();
const express = require("express");
const fs = require("fs");
const lighthouse = require("@lighthouse-web3/sdk");
const path = require("path");

const app = express();
const PORT = 3000;
const LOG_FILE = path.join(__dirname, "logs.json");
const OLD_LOGS_FOLDER = path.join(__dirname, "old_logs");
const LIGHTHOUSE_API_KEY = process.env.LIGHTHOUSE_API_KEY;

if (!fs.existsSync(OLD_LOGS_FOLDER)) {
	fs.mkdirSync(OLD_LOGS_FOLDER);
}

app.use(express.json());

function loadLogs() {
    return fs.existsSync(LOG_FILE) ? JSON.parse(fs.readFileSync(LOG_FILE)) : [];
}

function saveLogs(logs) {
    fs.writeFileSync(LOG_FILE, JSON.stringify(logs, null, 2));
}

app.post("/log", (req, res) => {
    try {
        const { name, camera_id, timestamp } = req.body;
        if (!name || !camera_id || !timestamp) {
            return res.status(400).json({ error: "Missing log fields" });
        }

        let logs = loadLogs();
        let existingLog = logs.find(log => log.name === name && log.camera_id === camera_id);

        if (existingLog) {
            existingLog.timestamp_end = timestamp;
        } else {
            logs.push({
                name,
                camera_id,
                timestamp_start: timestamp,
                timestamp_end: timestamp
            });
        }

        saveLogs(logs);
        res.json({ message: "Log received and compressed" });
    } catch (error) {
        console.error("❌ Error:", error);
        res.status(500).json({ error: "Server error" });
    }
});

async function uploadToLighthouse() {
	if (!fs.existsSync(LOG_FILE)) {
			console.log("⚠ No logs to upload.");
			return;
	}

	const logs = JSON.parse(fs.readFileSync(LOG_FILE, "utf-8"));
	if (logs.length === 0) {
			console.log("⚠ No logs to upload.");
			return;
	}

	const startTime = logs[0].timestamp_start.replace(/[:T]/g, "-"); 
	const endTime = logs[logs.length - 1].timestamp_end.replace(/[:T]/g, "-");

	const newFileName = `${startTime}_${endTime}.json`;
	const newFilePath = path.join(__dirname, newFileName);
	fs.renameSync(LOG_FILE, newFilePath);

	try {
			const response = await lighthouse.upload(newFilePath, LIGHTHOUSE_API_KEY);
			console.log(`✅ Logs uploaded to Lighthouse: ${response.data.Hash}`);

			fs.unlinkSync(newFilePath);
			return response.data.Hash;
	} catch (error) {
			console.error("❌ Failed to upload logs:", error.message);
	}
}

setInterval(uploadToLighthouse, 0.1 * 60 * 1000);

app.listen(PORT, () => {
    console.log(`🚀 Logging server running on http://localhost:${PORT}`);
});
