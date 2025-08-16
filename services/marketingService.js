const axios = require('axios');
const fs = require('fs');
const path = require('path');
const csv = require('fast-csv');
const { META_ACCESS_TOKEN, META_PHONE_NUMBER_ID, WHATSAPP_API_URL } = require('../config/credentials');
const { PROMO_LOG_CSV } = require('../config/settings');
const logger = require('../utils/logger');

function logPromo(to, message) {
  try {
    const filePath = path.resolve(PROMO_LOG_CSV || 'promo_sent_log.csv');
    const exists = fs.existsSync(filePath);
    const ws = fs.createWriteStream(filePath, { flags: 'a' });
    csv
      .write([
        { to, message, timestamp: new Date().toISOString() }
      ], { headers: !exists })
      .pipe(ws);
  } catch (err) {
    logger.error('Failed to log promo', { error: err.message });
  }
}

async function sendMarketingPromo(to, messageText) {
  try {
    await axios.post(
      WHATSAPP_API_URL || `https://graph.facebook.com/v20.0/${META_PHONE_NUMBER_ID}/messages`,
      {
        messaging_product: 'whatsapp',
        to,
        type: 'template',
        template: {
          name: 'promo_marketing',
          language: { code: 'en_US' },
          components: [
            {
              type: 'body',
              parameters: [{ type: 'text', text: messageText }]
            }
          ]
        }
      },
      {
        headers: {
          Authorization: `Bearer ${META_ACCESS_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );
    logger.info('Sent marketing promo', { to });
    logPromo(to, messageText);
  } catch (err) {
    logger.error('Failed to send marketing promo', { error: err.message });
  }
}

async function sendCatalogSet(to, retailerProductId) {
  try {
    await axios.post(
      WHATSAPP_API_URL || `https://graph.facebook.com/v20.0/${META_PHONE_NUMBER_ID}/messages`,
      {
        messaging_product: 'whatsapp',
        to,
        type: 'template',
        template: {
          name: 'set_cat',
          language: { code: 'en_US' },
          components: [
            {
              type: 'button',
              sub_type: 'CATALOG',
              index: 0,
              parameters: [
                {
                  type: 'action',
                  action: { thumbnail_product_retailer_id: retailerProductId }
                }
              ]
            }
          ]
        }
      },
      {
        headers: {
          Authorization: `Bearer ${META_ACCESS_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );
    logger.info('Sent catalog set', { to });
  } catch (err) {
    logger.error('Failed to send catalog set', { error: err.message });
  }
}

module.exports = { sendMarketingPromo, sendCatalogSet };
