const axios = require('axios');
const { META_ACCESS_TOKEN, META_PHONE_NUMBER_ID, WHATSAPP_API_URL } = require('../config/credentials');
const logger = require('../utils/logger');

async function sendTextMessage(to, body) {
  try {
    await axios.post(
      WHATSAPP_API_URL || `https://graph.facebook.com/v20.0/${META_PHONE_NUMBER_ID}/messages`,
      {
        messaging_product: 'whatsapp',
        to,
        type: 'text',
        text: { body }
      },
      {
        headers: {
          Authorization: `Bearer ${META_ACCESS_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );
    logger.info('Sent WhatsApp message', { to });
  } catch (err) {
    logger.error('Failed to send WhatsApp message', { error: err.message });
  }
}

async function sendTemplate(to, name, components = []) {
  try {
    await axios.post(
      WHATSAPP_API_URL || `https://graph.facebook.com/v20.0/${META_PHONE_NUMBER_ID}/messages`,
      {
        messaging_product: 'whatsapp',
        to,
        type: 'template',
        template: {
          name,
          language: { code: 'en_US' },
          components
        }
      },
      {
        headers: {
          Authorization: `Bearer ${META_ACCESS_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );
    logger.info('Sent template message', { to, name });
  } catch (err) {
    logger.error('Failed to send template', { error: err.message });
  }
}

async function sendPayOnlineTemplate(to, paymentLink) {
  const token = paymentLink && paymentLink.startsWith('https://rzp.io/rzp/')
    ? paymentLink.split('/').pop()
    : paymentLink;
  const components = [
    {
      type: 'button',
      sub_type: 'url',
      index: 0,
      parameters: [{ type: 'text', text: token }]
    }
  ];
  await sendTemplate(to, 'pays_online', components);
}

module.exports = { sendTextMessage, sendTemplate, sendPayOnlineTemplate };
