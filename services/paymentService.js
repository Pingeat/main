const axios = require('axios');
const { RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET } = require('../config/credentials');
const { getUserCart, setUserCart } = require('../stateHandlers/redisState');
const logger = require('../utils/logger');

async function generatePaymentLink(to, finalTotal, orderId) {
  try {
    const cart = await getUserCart(to);
    const existingLink = cart.payment_link;
    const lastTotal = cart.final_total;

    if (existingLink && lastTotal === finalTotal) {
      logger.info('Reusing existing payment link', { to, orderId });
      return existingLink;
    }

    const payload = {
      amount: Math.round((finalTotal || 0) * 100),
      currency: 'INR',
      accept_partial: false,
      reference_id: orderId,
      customer: { contact: to },
      notify: { sms: false, email: false },
      reminder_enable: true
    };

    const response = await axios.post(
      'https://api.razorpay.com/v1/payment_links',
      payload,
      {
        auth: {
          username: RAZORPAY_KEY_ID,
          password: RAZORPAY_KEY_SECRET
        }
      }
    );

    const link = response.data.short_url;
    cart.payment_link = link;
    cart.final_total = finalTotal;
    await setUserCart(to, cart);
    return link;
  } catch (err) {
    logger.error('Failed to generate payment link', { error: err.message });
    return null;
  }
}

module.exports = { generatePaymentLink };
