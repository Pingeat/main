const fs = require('fs');
const path = require('path');
const { sendTemplate } = require('./whatsappService');
const { FEEDBACK_CSV } = require('../config/settings');

// Send the feedback template to a WhatsApp user
function sendFeedbackTemplate(to) {
  // Template name assumed to be 'feedback_request'
  return sendTemplate(to, 'feedback_request');
}

// Schedule sending feedback template after a delay (default 30 minutes)
function scheduleFeedback(to, delayMs = 30 * 60 * 1000) {
  setTimeout(() => {
    sendFeedbackTemplate(to);
  }, delayMs);
}

// Save feedback entries to CSV file
function saveFeedback(phone, feedback) {
  const filePath = path.resolve(FEEDBACK_CSV || 'feedback.csv');
  const exists = fs.existsSync(filePath);
  const timestamp = new Date().toISOString();
  const line = `${phone},${feedback},${timestamp}\n`;
  if (!exists) {
    fs.writeFileSync(filePath, 'Phone,Feedback,Timestamp\n' + line);
  } else {
    fs.appendFileSync(filePath, line);
  }
}

module.exports = { scheduleFeedback, sendFeedbackTemplate, saveFeedback };
