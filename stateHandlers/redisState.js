const { createClient } = require('redis');
const logger = require('../utils/logger');

const client = createClient({ url: process.env.REDIS_URL || 'redis://localhost:6379' });
client.on('error', err => logger.error('Redis error', { error: err.message }));
client.connect().catch(err => logger.error('Redis connection failed', { error: err.message }));

async function getUserCart(phone) {
  const data = await client.get(`user_cart:${phone}`);
  return data ? JSON.parse(data) : {};
}

async function setUserCart(phone, cart) {
  await client.set(`user_cart:${phone}`, JSON.stringify(cart), { EX: 86400 });
}

async function deleteUserCart(phone) {
  await client.del(`user_cart:${phone}`);
}

async function getAllCarts() {
  const keys = await client.keys('user_cart:*');
  const result = {};
  for (const key of keys) {
    const data = await client.get(key);
    result[key.split(':')[1]] = JSON.parse(data);
  }
  return result;
}

async function getUserState(phone) {
  const data = await client.get(`user_state:${phone}`);
  return data ? JSON.parse(data) : {};
}

async function setUserState(phone, state) {
  await client.set(`user_state:${phone}`, JSON.stringify(state), { EX: 86400 });
}

async function deleteUserState(phone) {
  await client.del(`user_state:${phone}`);
}

async function addPendingOrder(orderId, data) {
  await client.set(`order:${orderId.toUpperCase()}`, JSON.stringify(data));
}

async function getPendingOrder(orderId) {
  const data = await client.get(`order:${orderId.toUpperCase()}`);
  return data ? JSON.parse(data) : null;
}

async function getPendingOrders() {
  const keys = await client.keys('order:*');
  const result = {};
  for (const key of keys) {
    const data = await client.get(key);
    result[key.split(':')[1]] = JSON.parse(data);
  }
  return result;
}

async function removePendingOrder(orderId) {
  await client.del(`order:${orderId.toUpperCase()}`);
}

module.exports = {
  client,
  getUserCart,
  setUserCart,
  deleteUserCart,
  getAllCarts,
  getUserState,
  setUserState,
  deleteUserState,
  addPendingOrder,
  getPendingOrder,
  getPendingOrders,
  removePendingOrder
};
