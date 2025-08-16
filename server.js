const express = require('express');
const crypto = require('crypto');
const dotenv = require('dotenv');
const logger = require('./utils/logger');
const { META_VERIFY_TOKEN, RAZORPAY_KEY_SECRET } = require('./config/credentials');
const { handleIncomingMessage } = require('./handlers/messageHandlers');
const { confirmOrder } = require('./services/orderService');
const { saveFeedback } = require('./services/feedbackService');
const { startJobs } = require('./scheduler/backgroundJobs');

dotenv.config();

const app = express();
app.use(express.json());

app.get('/webhook', (req, res) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];
  if (mode === 'subscribe' && token === META_VERIFY_TOKEN) {
    logger.info('Webhook verified');
    return res.status(200).send(challenge);
  }
  logger.warn('Webhook verification failed');
  return res.sendStatus(403);
});

app.post('/webhook', async (req, res) => {
  logger.info('Incoming webhook payload');
  try {
    await handleIncomingMessage(req.body);
  } catch (err) {
    logger.error('Error handling incoming message', { error: err.message });
  }
  res.sendStatus(200);
});

app.get('/payment-success', async (req, res) => {
  const whatsapp = req.query.whatsapp;
  const orderId = req.query.order_id;
  if (whatsapp && orderId) {
    await confirmOrder(whatsapp, 'Online', orderId, true);
  }
  res.status(200).send('Payment confirmed');
});

app.post('/razorpay-webhook-fruitcustard', express.raw({ type: 'application/json' }), (req, res) => {
  const receivedSignature = req.headers['x-razorpay-signature'] || '';
  const expected = crypto
    .createHmac('sha256', RAZORPAY_KEY_SECRET || '')
    .update(req.body)
    .digest('hex');
  if (!crypto.timingSafeEqual(Buffer.from(receivedSignature), Buffer.from(expected))) {
    logger.warn('Invalid Razorpay signature');
    return res.status(400).send('Invalid signature');
  }
  const data = JSON.parse(req.body.toString());
  if (data.event === 'payment_link.paid') {
    const payment = data.payload?.payment_link?.entity || {};
    const whatsapp = payment.customer?.contact;
    const orderId = payment.reference_id;
    if (whatsapp && orderId) {
      confirmOrder(whatsapp, 'Online', orderId, true);
    }
  }
  res.send('OK');
});

app.post('/feedback', (req, res) => {
  const { from, feedback, rating, comment } = req.body || {};
  try {
    const value = feedback || rating || comment || '';
    if (from && value) {
      saveFeedback(from, value);
    }
    res.sendStatus(200);
  } catch (err) {
    logger.error('Failed to save feedback', { error: err.message });
    res.sendStatus(500);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => logger.info(`Server listening on port ${PORT}`));
startJobs();

module.exports = app;
